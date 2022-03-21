# Copyright (c) 2021 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import cv2
from collections import defaultdict

from .det_infer import Detector, get_test_images, print_arguments, PredictConfig
from .visualize import plot_tracking_dict

from .mot.tracker import JDETracker
import threading
import base64
import numpy as np
import json

# Global dictionary
MOT_SUPPORT_MODELS = {
    'JDE',
    'FairMOT',
}


class JDE_Detector(Detector):
    """
    Args:
        pred_config (object): config of model, defined by `Config(model_dir)`
        model_dir (str): root path of model.pdiparams, model.pdmodel and infer_cfg.yml
        device (str): Choose the device you want to run, it can be: CPU/GPU/XPU, default is CPU
        run_mode (str): mode of running(fluid/trt_fp32/trt_fp16)
        batch_size (int): size of per batch in inference, default is 1 in tracking models
        trt_min_shape (int): min shape for dynamic shape in trt
        trt_max_shape (int): max shape for dynamic shape in trt
        trt_opt_shape (int): opt shape for dynamic shape in trt
        trt_calib_mode (bool): If the model is produced by TRT offline quantitative
            calibration, trt_calib_mode need to set True
        cpu_threads (int): cpu threads
        enable_mkldnn (bool): whether to open MKLDNN
    """

    def __init__(self,
                 pred_config,
                 model_dir,
                 device='CPU',
                 run_mode='fluid',
                 batch_size=1,
                 trt_min_shape=1,
                 trt_max_shape=1088,
                 trt_opt_shape=608,
                 trt_calib_mode=False,
                 cpu_threads=1,
                 enable_mkldnn=False):
        super(JDE_Detector, self).__init__(
            pred_config=pred_config,
            model_dir=model_dir,
            device=device,
            run_mode=run_mode,
            batch_size=batch_size,
            trt_min_shape=trt_min_shape,
            trt_max_shape=trt_max_shape,
            trt_opt_shape=trt_opt_shape,
            trt_calib_mode=trt_calib_mode,
            cpu_threads=cpu_threads,
            enable_mkldnn=enable_mkldnn)
        assert batch_size == 1, "The JDE Detector only supports batch size=1 now"
        assert pred_config.tracker, "Tracking model should have tracker"
        self.num_classes = len(pred_config.labels)

        tp = pred_config.tracker
        min_box_area = tp['min_box_area'] if 'min_box_area' in tp else 200
        vertical_ratio = tp['vertical_ratio'] if 'vertical_ratio' in tp else 1.6
        conf_thres = tp['conf_thres'] if 'conf_thres' in tp else 0.
        tracked_thresh = tp['tracked_thresh'] if 'tracked_thresh' in tp else 0.7
        metric_type = tp['metric_type'] if 'metric_type' in tp else 'euclidean'

        self.tracker = JDETracker(
            num_classes=self.num_classes,
            min_box_area=min_box_area,
            vertical_ratio=vertical_ratio,
            conf_thres=conf_thres,
            tracked_thresh=tracked_thresh,
            metric_type=metric_type)

    def postprocess(self, pred_dets, pred_embs, threshold):
        online_targets_dict = self.tracker.update(pred_dets, pred_embs)

        online_tlwhs = defaultdict(list)
        online_scores = defaultdict(list)
        online_ids = defaultdict(list)
        for cls_id in range(self.num_classes):
            online_targets = online_targets_dict[cls_id]
            for t in online_targets:
                tlwh = t.tlwh
                tid = t.track_id
                tscore = t.score
                if tscore < threshold: continue
                if tlwh[2] * tlwh[3] <= self.tracker.min_box_area:
                    continue
                if self.tracker.vertical_ratio > 0 and tlwh[2] / tlwh[
                        3] > self.tracker.vertical_ratio:
                    continue
                online_tlwhs[cls_id].append(tlwh)
                online_ids[cls_id].append(tid)
                online_scores[cls_id].append(tscore)
        return online_tlwhs, online_scores, online_ids

    def predict(self, image_list, threshold=0.5, warmup=0, repeats=1):
        '''
        Args:
            image_list (list[str]): path of images, only support one image path
                (batch_size=1) in tracking model
            threshold (float): threshold of predicted box' score
        Returns:
            online_tlwhs, online_scores, online_ids (dict[np.array])
        '''
        self.det_times.preprocess_time_s.start()
        inputs = self.preprocess(image_list)
        self.det_times.preprocess_time_s.end()

        pred_dets, pred_embs = None, None
        input_names = self.predictor.get_input_names()
        for i in range(len(input_names)):
            input_tensor = self.predictor.get_input_handle(input_names[i])
            input_tensor.copy_from_cpu(inputs[input_names[i]])

        for i in range(warmup):
            self.predictor.run()
            output_names = self.predictor.get_output_names()
            boxes_tensor = self.predictor.get_output_handle(output_names[0])
            pred_dets = boxes_tensor.copy_to_cpu()

        self.det_times.inference_time_s.start()
        for i in range(repeats):
            self.predictor.run()
            output_names = self.predictor.get_output_names()
            boxes_tensor = self.predictor.get_output_handle(output_names[0])
            pred_dets = boxes_tensor.copy_to_cpu()
            embs_tensor = self.predictor.get_output_handle(output_names[1])
            pred_embs = embs_tensor.copy_to_cpu()
        self.det_times.inference_time_s.end(repeats=repeats)

        self.det_times.postprocess_time_s.start()
        online_tlwhs, online_scores, online_ids = self.postprocess(
            pred_dets, pred_embs, threshold)
        self.det_times.postprocess_time_s.end()
        self.det_times.img_num += 1

        return online_tlwhs, online_scores, online_ids


class VideoReadThread(threading.Thread):
    def __init__(self, func, video_path, model_dir, thrd):
        threading.Thread.__init__(self)
        self.running_status = False
        self.vpath = video_path
        self.cb_func = func
        self.thrd = thrd
        self.model_dir = model_dir

        # AI model
        pred_config = PredictConfig(model_dir)
        self.detector = JDE_Detector(
            pred_config,
            model_dir,
            device="GPU",
            run_mode="fluid",
            trt_min_shape=1,
            trt_max_shape=1280,
            trt_opt_shape=640,
            trt_calib_mode=False,
            cpu_threads=1,
            enable_mkldnn=False)

    def run(self):
        capture = cv2.VideoCapture(self.vpath)
        if not capture.isOpened():
            print('no video')
            return

        self.running_status = True
        frame_id = 0
        while self.running_status:
            ret, frame = capture.read()
            if not ret:
                break

            self.predict_video(frame, frame_id)
            frame_id += 1
            # time.sleep(10)

    def stop(self):
        self.running_status = False

    def predict_video(self, frame, frame_id):
        t1 = time.time()
        online_tlwhs, online_scores, online_ids = self.detector.predict(
            [frame], self.thrd)
        print("frame time cost: ", time.time() - t1)

        im = plot_tracking_dict(
            frame,
            1,
            online_tlwhs,
            online_ids,
            online_scores,
            frame_id=frame_id,
            fps=1,
            ids2names=self.detector.pred_config.labels,
            do_entrance_counting=False,
            entrance=None,
            records=None,
            center_traj=None)

        height, width = im.shape[:2]
        size = (int(width * 0.5), int(height * 0.5))
        frame = cv2.resize(im, size, interpolation=cv2.INTER_AREA)

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        result, imgencode = cv2.imencode('.jpg', frame, encode_param)
        data = np.array(imgencode)
        img = data.tobytes()
        img = base64.b64encode(img).decode()

        send_data = json.dumps({"type": "images", "value": "data:image/jpeg;base64," + img})
        self.cb_func(send_data)


