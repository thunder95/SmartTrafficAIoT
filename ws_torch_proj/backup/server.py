import asyncio
import websockets
import json
import cv2
import base64
import numpy as np

USERS = {} #clients
IS_VIDEO_OPEN = False
async def start(websocket,pem):
    capture = cv2.VideoCapture(pem['values'])
    if not capture.isOpened():
        print('no video')
        return

    IS_VIDEO_OPEN = True
    while IS_VIDEO_OPEN:
        ret, frame = capture.read()
        if not ret:
            break
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        result, imgencode = cv2.imencode('.jpg', frame, encode_param)
        data = np.array(imgencode)
        img = data.tobytes()
        img = base64.b64encode(img).decode()
        await websocket.send(json.dumps({"type":"images", "value":"data:image/jpeg;base64," + img}))

    print("video over")

async def stop(websocket,pem):
    # USERS.update({websocket:pem['values']})
    # print(USERS)
    IS_VIDEO_OPEN = False
    print("stop ok")

async def command(websocket,pem):
    # USERS.update({websocket:pem['values']})
    # print(USERS)
    print("command")


# async def send_count_users():
#     if USERS:
#         message = user_event()
#         await asyncio.wait([user.send(message) for user in USERS])

# async def del_users(websocket):
#     del USERS[websocket]
#     await send_count_users()

# async def send_to_users(message,websocket):
#     if USERS:
#         message = json.dumps({"type": "message", "user": USERS[websocket] , "value": message})
#         await asyncio.wait([user.send(message) for user in USERS])



async def server(websocket,path):
    # await reg_users(websocket)
    try:
        await data(websocket)
    finally:
        # await del_users(websocket)
        # print(USERS)
        print("over")

async def data(websocket):
     async for message in websocket:
        print(111)
        pem = json.loads(message)
        if pem['action'] == 'start':
            start(websocket, pem)
        elif pem['action'] =='stop':
            stop(websocket, pem)
        elif pem['action'] =='command':
            command(websocket, pem)
     print("data over...")


start_server = websockets.serve(server, '127.0.0.1', 5678)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
