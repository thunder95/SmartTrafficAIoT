import cv2
import numpy as np
from paddle.vision.image
"""
0: image normal, 1: image too dark, 2: image too bright
"""
def check_brightness(img):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 获取形状以及长宽
    img_shape = gray_img.shape
    height, width = img_shape[0], img_shape[1]
    size = gray_img.size
    # 灰度图的直方图
    hist = cv2.calcHist([gray_img], [0], None, [256], [0, 256])
    # 计算灰度图像素点偏离均值(128)程序
    ma = 0
    reduce_matrix = np.full((height, width), 128)
    shift_value = gray_img - reduce_matrix
    shift_sum = sum(map(sum, shift_value))

    da = shift_sum / size

    # 计算偏离128的平均偏差
    for i in range(256):
        ma += (abs(i - 128 - da) * hist[i])
    m = abs(ma / size)
    # 亮度系数
    k = abs(da) / m
    # print(k)
    if k[0] > 1:
        # 过亮
        if da > 0:
            return 2
        else:
            return 1
    else:
        return 0

if __name__ == "__main__":
    img = cv2.imread("/home/hulei/Kazam_screenshot_00001.png")
    print(check_brightness(img))