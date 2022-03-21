import asyncio
import websockets
import json
import cv2
import base64
import numpy as np
import threading

class VideoReadThread(threading.Thread):
    def __init__(self, video_path, websocket):
        threading.Thread.__init__(self)
        self.running_status = False
        self.vpath = video_path
        self.ws = websocket
        # todo AI model

    async def run(self):
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
            await self.send(img)
        print("run over...")

    def stop(self):
        print("stopping...video")
        self.running_status = False

    async def send(self, img):
        await self.ws.send(json.dumps({"type": "images", "value": "data:image/jpeg;base64," + img}))

class WebsocketsServer:
    def __init__(self):
        start_server = websockets.serve(self.server, '127.0.0.1', 5678)
        asyncio.get_event_loop().run_until_complete(start_server)
        self.video_thrd = None
        print("ws finish init")

    async def server(self, websocket, path):
        try:
            await self.data(websocket)
        finally:
            print("over")

    async def start(self, websocket, pem):
        self.video_thrd = VideoReadThread(pem["values"], websocket)
        self.video_thrd.start()
        print("start finish")

    async def stop(self, websocket, pem):
        print("stop ok")
        if self.video_thrd:
            self.video_thrd.stop()
            self.video_thrd.join()
            self.video_thrd = None

    async def command(self, websocket, pem):
        print("command")

    async def data(self, websocket):
        async for message in websocket:
            print(111)
            pem = json.loads(message)
            if pem['action'] == 'start':
                await self.start(websocket, pem)
            elif pem['action'] =='stop':
                await self.stop(websocket, pem)
            elif pem['action'] =='command':
                self.command(websocket, pem)

if __name__ == '__main__':
    wss = WebsocketsServer()
    asyncio.get_event_loop().run_forever()
    print("exit")