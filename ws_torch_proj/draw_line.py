import numpy as np
import cv2

#监听鼠标按下
btn_down = False
lines_data = []
cur_color = (0,255,0)

poly_color = (255, 255, 0)
poly_data = []

#画进入线和离开线
def draw_line(frame):

    def get_points(im):
        # Set the callback function for any mouse event
        global lines_data, cur_color
        lines_data = []
        cur_color = (0, 255, 0)
        im_copy = im.copy()
        cv2.imshow("Image", im_copy)
        cv2.setMouseCallback("Image", mouse_handler, im_copy)

    def mouse_handler(event, x, y, flags, img):
        global btn_down, lines_data, cur_color

        if event == cv2.EVENT_LBUTTONUP and btn_down:
            #if you release the button, finish the line
            btn_down = False
            lines_data[0].append([int(x), int(y)]) #append the seconf point
            cv2.circle(img, (x, y), 3, cur_color,5)
            cv2.line(img, tuple(lines_data[0][0]), tuple(lines_data[0][1]), cur_color, 2)
            cur_color = (255,0,0)
            cv2.imshow("Image", img)

        elif event == cv2.EVENT_MOUSEMOVE and btn_down:
            #thi is just for a ine visualization
            image = img.copy()
            cv2.line(image, tuple(lines_data[0][0]), (int(x), int(y)), cur_color, 1)
            cv2.imshow("Image", image)

        elif event == cv2.EVENT_LBUTTONDOWN and len(lines_data) < 2:
            btn_down = True
            lines_data.insert(0,[(int(x), int(y))]) #prepend the point
            # lines_data.append([(int(x), int(y))])
            cv2.circle(img, (x, y), 3, cur_color, 5, 16)
            cv2.imshow("Image", img)


    # Running the code
    while True:
        if len(lines_data) >= 2:
            break

        get_points(frame) #画点
        k = cv2.waitKey(0) & 0xFF
        if k == 13:
            # print("saved", pts)
            cv2.destroyAllWindows()
            return lines_data #enter, 表示确认
        elif k == ord('c'):
            print('cancel')
            btn_down = False
            continue #c表示取消, 重新绘制
        elif k == ord('q'):
            print('quit')
            return [] #强制退出




if __name__ == '__main__':
    capture=cv2.VideoCapture("/d/hulei/hw_mqtt_py/mp4_files/night_clip.mp4")
    ref,frame=capture.read()
    rs = draw_line(frame)[0]
    print(rs)

    # h, w, _  = frame.shape
    # print(w, h)
    #
    # pts = []
    # pts.append(str(rs[0][0] / float(w)))
    # pts.append(str(rs[0][1] / float(h)))
    # pts.append(str(rs[1][0] / float(w)))
    # pts.append(str(rs[1][1] / float(h)))
    # print("drawed pts: ", ",".join(pts)) #0.5421875,0.42361,0.996875,0.6583
