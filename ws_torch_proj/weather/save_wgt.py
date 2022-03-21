from torchvision.models import resnet18
import torch

torch_model = resnet18(num_classes = 5)

wgts = torch_model.state_dict()

# print(wgts.keys())

import paddle

wgts2 = paddle.load("final.pdparams")
# print(wgts2.keys())

suffix_map = {".running_mean": "._mean", ".running_var": "._variance", ".num_batches_tracks": None}
for w in wgts:

    if ".running_mean" in w:
        w2 = w.replace(".running_mean", "._mean")
    elif ".running_var" in w:
        w2 = w.replace(".running_var", "._variance")
    else:
        w2 = w

    if w2 in wgts2:
        # print(wgts[w])
        tmp_wgt = wgts2[w2].numpy()
        if "fc." in w:
            wgts[w] = torch.from_numpy(tmp_wgt.transpose())
        else:
            wgts[w] = torch.from_numpy(tmp_wgt)
    else:
        print(w2)

torch_model.load_state_dict(wgts)
torch.save(torch_model.state_dict(), "weather.pt")
