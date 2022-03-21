import paddle
import paddle.vision.transforms as T
import cv2
import numpy as np

class WeatherType:
    def __init__(self):

        # 预处理
        self.test_transforms = T.Compose([
            T.Resize((224, 224), interpolation='bicubic'),
            T.ToTensor(),
            T.Normalize()
        ])

        # 网络结构示例化
        self.model = paddle.Model(paddle.vision.models.resnet18(num_classes=5))
        self.model.load("60.pdparams")

    def preprocess(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return paddle.unsqueeze(self.test_transforms(img), axis=0)

    def infer(self, img):
        data = self.preprocess(img)
        output = self.model.predict_batch(data)
        out = np.argmax(output[0], axis=-1)
        return out[0]

if __name__ == "__main__":
    wt = WeatherType()
    wt.infer(cv2.imread("Image16960.jpg"))