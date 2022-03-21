# -*- encoding: utf-8 -*-
'''
消息传送demo
包括订阅topic
发布消息
'''

import logging
import json

from IoT_device.client import IoTClientConfig
from IoT_device.client import IotClient

# 日志设置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IoTService:
    def __init__(self, command_cb):
        # 客户端配置
        self.client_cfg = IoTClientConfig(server_ip='myhuaweicloud.com',
                                     device_id='pylight',
                                     secret='01', is_ssl=True)
        # 创建设备
        self.iot_client = IotClient(self.client_cfg)
        self.iot_client.connect()  # 建立连接

        # 发送到前端显示
        self.cb_func = command_cb
        self.iot_client.start()
    def command_callback(self,request_id, command):
        logger.info(('Command, device id:  ', command.device_id))
        logger.info(('Command, service id = ', command.service_id))
        logger.info(('Command, command name: ', command.command_name))
        logger.info(('Command. paras: ', command.paras))
        # result_code:设置为零相应命令下发成功，为 1 下发命令失败
        self.iot_client.respond_command(request_id, result_code=0)
        print('------------------this is myself callback')

        send_data = json.dumps({"type": "images", "value": "1"})
        self.cb_func(send_data)

    def publish_message(self, msg):
        self.iot_client.publish_message(r'$oc/devices/' + str(self.client_cfg.device_id) + r'/user/wpy/up', msg)

def test_cb(msg):
    print(msg)

if __name__ == "__main__":
    iot = IoTService(test_cb)
    iot.publish_message("2222")
