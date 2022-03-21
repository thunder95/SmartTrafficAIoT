import torch
from torchvision.models import resnet18
import cv2
import numpy as np

class WeatherType:
    def __init__(self):

        # 网络结构示例化
        self.model = resnet18(num_classes=5,pretrained=False)
        self.model.load_state_dict(torch.load('weights/weather.pt'))
        self.model.eval()

    def preprocess(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (224, 224), cv2.INTER_CUBIC)
        img = img.transpose((2, 0, 1)) / 255.0
        return torch.unsqueeze(torch.from_numpy(img), dim=0).to(torch.float32)

    def infer(self, img):
        data = self.preprocess(img)
        # print(data)
        # data = torch.from_numpy(np.load("input.npy"))
        output = self.model(data)
        out = torch.argmax(output[0], dim=-1).detach().cpu().numpy()
        return int(out)

if __name__ == "__main__":
    wt = WeatherType()
    print(wt.infer(cv2.imread("sunny_02059.jpg")))