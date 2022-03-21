# from fairmot.deploy.pptracking.python.fairmot_infer import VehicleTracker
#
# vt = VehicleTracker("./fairmot/models/fairmot_hrnetv2_w18_dlafpn_30e_576x320_bdd100kmot_vehicle", 0.3, "348,364,1653,322")

from yolov5_deepsort.AIDetector_pytorch import Detector
import imutils
import cv2
import time


def main():
    name = 'demo'

    det = Detector()
    cap = cv2.VideoCapture('mp4_files/foggy.mp4')
    fps = int(cap.get(5))
    print('fps:', fps)
    t = int(1000 / fps)

    videoWriter = None
    is_odd = False
    while True:

        # try:
        _, im = cap.read()
        if im is None:
            break
        """
        if is_odd:
            is_odd = not is_odd
            continue
        is_odd = not is_odd
        """
        s = time.time()
        result = det.feedCap(im)
        print(time.time() - s)

        print(result)
        break

        result = result['frame']
        result = imutils.resize(result, height=500)


        # videoWriter.write(result)
        cv2.imshow(name, result)
        cv2.waitKey(t)

        if cv2.getWindowProperty(name, cv2.WND_PROP_AUTOSIZE) < 1:
            # 点x退出
            break
        # except Exception as e:
        #     print(e)
        #     break

    cap.release()
    # videoWriter.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
