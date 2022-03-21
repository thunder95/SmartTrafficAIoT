import json
import cv2
import base64
import numpy as np
import threading
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

class VideoReadThread(threading.Thread):
    def __init__(self, func, video_path):
        threading.Thread.__init__(self)
        self.running_status = False
        self.vpath = video_path
        self.cb_func = func
        # todo AI model

    def run(self):
        capture = cv2.VideoCapture(self.vpath)
        if not capture.isOpened():
            print('no video')
            return

        self.running_status = True
        while self.running_status:
            ret, frame = capture.read()
            if not ret:
                break
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            result, imgencode = cv2.imencode('.jpg', frame, encode_param)
            data = np.array(imgencode)
            img = data.tobytes()
            img = base64.b64encode(img).decode()

            send_data = json.dumps({"type":"images", "value":"data:image/jpeg;base64," + img})
            self.cb_func(send_data)
            # time.sleep(10)

    def stop(self):
        self.running_status = False


class WsServer(WebSocket):
    video_thrd = None
    def handleMessage(self):
        # echo message back to client
        tmp = json.loads(self.data)
        if tmp["action"] == "start":
            self.video_thrd = VideoReadThread(self.sendMsg, tmp["values"])
            self.video_thrd.start()
        elif tmp["action"] == "stop":
            self.video_thrd.stop()
            self.video_thrd.join()

    def handleConnected(self):
        print(self.address, 'connected')

    def handleClose(self):
        print(self.address, 'closed')

    def sendMsg(self, msg):
        self.sendMessage(msg)

if __name__ == '__main__':
    server = SimpleWebSocketServer('', 5678, WsServer)
    server.serveforever()
