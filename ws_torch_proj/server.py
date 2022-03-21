import json
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from AIDetector_pytorch import Detector
from iot_service import IoTService
import cv2
import threading
from weather.weather_type import WeatherType
from AIDetector_pytorch import Detector
import numpy as np
import base64

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkiotda.v5.region.iotda_region import IoTDARegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkiotda.v5 import *
import requests


class VideoReadThread(threading.Thread):
    def __init__(self, msg_func, iot_func):
        threading.Thread.__init__(self)
        self.running_status = False
        self.tracker = Detector()
        self.weather_predictor = WeatherType()
        self.msg_func = msg_func
        self.iot_func = iot_func
        self.last_green_send=0

    def setVal(self, video_path, entry_pts):
        self.vpath = video_path
        pts = entry_pts.split(",") # [[348, 364], [1653, 322]]
        self.entrance = [[int(pts[0].strip()), int(pts[1].strip())], [int(pts[2].strip()), int(pts[3].strip())]]
        self.track_pts = {}  # track_id, init_status (0, 1)
        self.in_tids = []  # 已统计驶向的跟踪id
        self.out_tids = []  # 已统计驶出的跟踪id

    def run(self):
        # 获取第三方app城市天气
        app_key = ""
        r = requests.get('https://way.jd.com/jisuapi/weather?city=成都&cityid=321&citycode=101270101&appkey='+app_key)
        data = r.json()
        if data["code"] == '10000':
            res = data["result"]["result"]
            send_data = {'Temperature': float(res["temp"]), 'PM_25': float(res["aqi"]["pm2_5"]), 'Humidity':float(res["humidity"])}
            self.iot_func("Basic", send_data)

        capture = cv2.VideoCapture(self.vpath)
        if not capture.isOpened():
            print('no video')
            return

        self.running_status = True
        frame_id = 0
        print("===> start video", self.vpath)

        last_weather_cnt = 0
        last_weather_type = None
        while self.running_status:
            ret, frame = capture.read()
            if not ret:
                break

            if frame_id % 10 == 0:
                wtype = self.weather_predictor.infer(frame)
                if last_weather_type == wtype:
                    last_weather_cnt += 1
                else:
                    last_weather_cnt = 0
                last_weather_type = wtype

                if last_weather_cnt >= 5:
                    self.iot_func("Weather", {"WeatherType": wtype})
                    last_weather_cnt=0

            self.predict_tracker(frame)
            frame_id += 1

    def stop(self):
        self.running_status = False

    def predict_tracker(self, frame):
        res_img, ct_pts = self.tracker.feedCap(frame)
        if res_img is not None:
            # 画进出线
            cv2.line(res_img, tuple(self.entrance[0]), tuple(self.entrance[1]), (0, 0, 255), 2)

            height, width = res_img.shape[:2]
            size = (int(width * 0.5), int(height * 0.5))
            res_img = cv2.resize(res_img, size, interpolation=cv2.INTER_AREA)

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            result, imgencode = cv2.imencode('.jpg', res_img, encode_param)
            data = np.array(imgencode)
            img = data.tobytes()
            res_img = base64.b64encode(img).decode()
            send_data = json.dumps({"type": "images", "value": "data:image/jpeg;base64," + res_img})
            self.msg_func(send_data)

        cnt_in = 0
        cnt_out = 0
        for pt in ct_pts: # cx, cy, tid
            if pt[2] < 0: continue
            check_res = self.check_line(pt[2], pt[0], pt[1])
            if check_res is None:
                continue

            if check_res > 0:
                cnt_in += 1
            elif check_res < 0:
                cnt_out += 1

        if cnt_in > 0 or cnt_out > 0:
            self.iot_func("Vehicle", {"After": cnt_out, "Forward": cnt_in, "Num": len(ct_pts)})
            self.last_green_send += 1

            if self.last_green_send % 30 == 0:
                self.last_green_send = 0
                send_data = json.dumps({"type": "carNum", "value": len(ct_pts)})
                self.msg_func(send_data)


    def get_direction(self, cx, cy):
        if ((self.entrance[0][0] - cx) * (self.entrance[1][1] - cy) - (self.entrance[0][1] - cy) * (self.entrance[1][0] - cx)) > 0:
            return 1
        return -1

    def check_line(self, tid, cx, cy):
        direct = self.get_direction(cx, cy)
        if tid not in self.track_pts:
            self.track_pts[tid] = direct

        if direct == self.track_pts[tid]:
            return None

        return direct

class WsServer(WebSocket):

    def handleMessage(self):
        # echo message back to client
        tmp = json.loads(self.data)
        if tmp["action"] == "start":
            self.video_thrd = VideoReadThread(self.sendMsg, self.sendIoT)
            self.iot = IoTService(self.sendMsg)
            ak = ""
            sk = ""
            credentials = BasicCredentials(ak, sk)
            self.iot_app = IoTDAClient.new_builder().with_credentials(credentials).with_region(IoTDARegion.value_of("cn-north-4")).build()
            self.video_thrd.setVal(tmp["values"], tmp["pts"])
            self.video_thrd.start()

        elif tmp["action"] == "stop":
            self.video_thrd.stop()
            self.video_thrd.join()

        elif tmp["action"] == "command":
            self.sendCommand(tmp["type"], tmp["values"])

    def handleConnected(self):
        print(self.address, 'connected')

    def handleClose(self):
        print(self.address, 'closed')

    def sendMsg(self, msg):
        self.sendMessage(msg)

    def sendIoT(self, msg_type, msg_value):
        if self.iot:
            self.iot.update_property(msg_type, msg_value)

    def sendCommand(self, cmd_type, cmd_value):
        request = CreateCommandRequest()
        request.device_id = "traffic_03"

        if cmd_type == "Green_control":
            request.body = DeviceCommandRequest(
                paras={"green_light_time": cmd_value},
                command_name="Green_control",
                service_id="Vehicle"
            )
        elif cmd_type == "Light_ON":
            request.body = DeviceCommandRequest(
                paras={"light_on": cmd_value},
                command_name=cmd_type,
                service_id="Weather"
            )
        elif cmd_type == "Yellow_ON":
            request.body = DeviceCommandRequest(
                paras={"yellow_on": cmd_value},
                command_name=cmd_type,
                service_id="Weather"
            )
        else:
            return

        response = self.iot_app.create_command(request)
        print(response)

def func1(msg):
    pass

def fun2(msg):
    pass
if __name__ == '__main__':
    server = SimpleWebSocketServer('', 5678, WsServer)
    server.serveforever()
    #
    # vr = VideoReadThread(func1, fun2, "/d/hulei/hw_mqtt_py/websocket_chat-main/fairmot/output/c003.mp4", "348,364,1653,322")
    # vr.start()

