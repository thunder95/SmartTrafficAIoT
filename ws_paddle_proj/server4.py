import json
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from fairmot.deploy.pptracking.python.fairmot_infer import VideoReadThread
from iot_service import IoTService


class WsServer(WebSocket):
    video_thrd = None
    iot = None
    def handleMessage(self):
        # echo message back to client
        tmp = json.loads(self.data)
        if tmp["action"] == "start":
            self.iot = IoTService(self.sendMsg)
            self.video_thrd = VideoReadThread(self.sendMsg, tmp["values"], "./fairmot/models/fairmot_hrnetv2_w18_dlafpn_30e_576x320_bdd100kmot_vehicle", 0.3)
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

        if self.iot:
            self.iot.publish_message("111")

if __name__ == '__main__':
    server = SimpleWebSocketServer('', 5678, WsServer)
    server.serveforever()
