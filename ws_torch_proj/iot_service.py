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
from IoT_device.request.services_properties import ServicesProperties


# 日志设置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IoTService:
    def __init__(self, command_cb):
        # 客户端配置
        self.client_cfg = IoTClientConfig(server_ip='iot-mqtts.cn-north-4.myhuaweicloud.com',
                                     device_id='traffic_03',
                                     secret='xxxx', is_ssl=True)
        # 创建设备
        self.iot_client = IotClient(self.client_cfg)
        self.iot_client.connect()  # 建立连接

        self.iot_client.set_command_callback(self.command_callback)

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

        command_str = ""
        if command.command_name == "Green_control":
            command_str = "命令下发, 调整绿灯时长: " + str(command.paras["green_light_time"]) + "秒"
        elif command.command_name == "Light_ON":
            command_str = "命令下发, " + ("打开路灯" if str(command.paras["light_on"]) == "1" else "关闭路灯")
        elif command.command_name == "Yellow_ON":
            command_str = "命令下发, " + ("因恶劣天气:开启黄灯" if str(command.paras["yellow_on"]) == "1" else "关闭黄灯")

        send_data = json.dumps({"type": "commands", "value": command_str})
        self.cb_func(send_data)

    def update_vehicle_property(self, in_num, out_num, total_num):
        service_property = ServicesProperties()
        service_property.add_service_property(service_id="Vehicle", property='After', value=out_num)
        service_property.add_service_property(service_id="Vehicle", property='Forward', value=in_num)
        service_property.add_service_property(service_id="Vehicle", property='Num', value=total_num)
        self.iot_client.report_properties(service_properties=service_property.service_property, qos=1)

    def update_env_property(self, temp, hum, pm):
        service_property = ServicesProperties()
        service_property.add_service_property(service_id="Basic", property='PM2.5', value=pm)
        service_property.add_service_property(service_id="Basic", property='Temperature', value=temp)
        service_property.add_service_property(service_id="Basic", property='Humidity', value=hum)
        self.iot_client.report_properties(service_properties=service_property.service_property, qos=1)

    def update_weahter_property(self, wType):
        service_property = ServicesProperties()
        service_property.add_service_property(service_id="Weather", property='WeatherType', value=wType)
        self.iot_client.report_properties(service_properties=service_property.service_property, qos=1)

    def update_property(self, data_type, data_values):
        print(data_type, data_values)
        service_property = ServicesProperties()
        for dk in data_values:
            service_property.add_service_property(service_id=data_type, property=dk, value=data_values[dk])
        self.iot_client.report_properties(service_properties=service_property.service_property, qos=1)


def test_cb(msg):
    print(msg)

if __name__ == "__main__":
    iot = IoTService(test_cb)
    iot.publish_message("2222")
