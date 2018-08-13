"""
# author: shiyipaisizuo
# contact: shiyipaisizuo@gmail.com
# file: train.py
# time: 2018/8/13 09:23
# license: MIT
"""

import argparse
import os
import time
import numpy as np
import cv2
import torch
from torch.autograd import Variable
import torchvision
from torch import nn
from torch import optim
from torchvision import transforms

from PIL import Image

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

parser = argparse.ArgumentParser("""Image classifical!""")
parser.add_argument('--path', type=str, default='../data/catdog/',
                    help="""image dir path default: '../data/catdog/'.""")
parser.add_argument('--epochs', type=int, default=50,
                    help="""Epoch default:50.""")
parser.add_argument('--batch_size', type=int, default=5,
                    help="""Batch_size default:5.""")
parser.add_argument('--lr', type=float, default=0.0001,
                    help="""learing_rate. Default=0.0001""")
parser.add_argument('--model_path', type=str, default='../../model/pytorch/',
                    help="""Save model path""")
parser.add_argument('--model_name', type=str, default='catdog.pth',
                    help="""Model name.""")
parser.add_argument('--display_epoch', type=int, default=2)
args = parser.parse_args()

# Create model
if not os.path.exists(args.model_path):
    os.makedirs(args.model_path)

transform = transforms.Compose([
    transforms.Resize(128),  # 将图像转化为800 * 800
    transforms.RandomHorizontalFlip(p=0.75),  # 有0.75的几率随机旋转
    transforms.RandomCrop(114),  # 从图像中裁剪一个24 * 24的
    transforms.ColorJitter(brightness=1, contrast=2, saturation=3, hue=0),  # 给图像增加一些随机的光照
    # transforms.Grayscale(),  # 转化为灰度图
    transforms.ToTensor(),  # 将numpy数据类型转化为Tensor
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # 归一化
])

# Load data
train_datasets = torchvision.datasets.ImageFolder(root=args.path + 'train/',
                                                  transform=transform)
val_datasets = torchvision.datasets.ImageFolder(root=args.path + 'val/',
                                                transform=transform)

datasets = torchvision.datasets.ImageFolder
train_loader = torch.utils.data.DataLoader(dataset=train_datasets,
                                           batch_size=args.batch_size,
                                           shuffle=True)

val_loader = torch.utils.data.DataLoader(dataset=val_datasets,
                                         batch_size=args.batch_size,
                                         shuffle=True)

num_classes = 2


# Create neural net
class Net(nn.Module):
    def __init__(self, category=num_classes):
        super(Net, self).__init__()
        self.features = nn.Sequential(
            # Conv 1
            nn.Conv2d(3, 64, 3, 1, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2),

            # Conv 2

            nn.Conv2d(64, 128, 3, 1, 1),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2),
            nn.MaxPool2d(2, 2),

            # Conv 3
            nn.Conv2d(128, 256, 3, 1, 1),
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2),

            # Conv 4
            nn.Conv2d(256, 512, 3, 1, 1),
            nn.BatchNorm2d(512),
            nn.ReLU(True),

            # Conv 5
            nn.Conv2d(512, 512, 3, 1, 1),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2)
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.75),
            nn.Linear(512 * 3 * 3, 512),
            nn.ReLU(True),

            nn.Dropout(0.75),
            nn.Linear(512, 256),
            nn.ReLU(True),

            nn.Linear(256, category)
        )

    def forward(self, x):
        out = self.features(x)

        dense = out.reshape(x.size(0), -1)

        out = self.classifier(dense)

        return out


def train():
    print(f"Train numbers:{len(train_datasets)}")
    print(f"Val numbers:{len(val_datasets)}")

    # Load model
    model = Net().to(device)
    print(model)
    # cast
    cast = nn.CrossEntropyLoss()
    # Optimization
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    for epoch in range(1, args.epochs + 1):
        model.train()
        start = time.time()
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            # Forward pass
            outputs = model(images)
            loss = cast(outputs, labels)

            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        if epoch % args.display_epoch == 0:
            end = time.time()
            print(f"Epoch [{epoch}/{args.epochs}], "
                  f"Loss: {loss.item():.8f}, "
                  f"Time: {(end-start) * args.display_epoch:.1f}sec!")
            test()

    # Save the model checkpoint
    torch.save(model, args.model_path + args.model_name)
    print(f"Model save to {args.model_path + args.model_name}.")


def test():
    print(f"test numbers: {len(val_datasets)}.")
    model = torch.load(args.model_path + args.model_name)
    model.eval()

    correct_prediction = 0.
    total = 0
    for images, labels in val_loader:
        # to GPU
        images = images.to(device)
        labels = labels.to(device)
        # print prediction
        outputs = model(images)
        # equal prediction and acc
        _, predicted = torch.max(outputs.data, 1)
        # val_loader total
        total += labels.size(0)
        # add correct
        correct_prediction += (predicted == labels).sum().item()

    print(f"Acc: {(correct_prediction / total):4f}")


def val(img):
    model = torch.load(args.model_path + args.model_name)

    model.eval()
    img = cv2.imread(img)
    img = torch.Tensor(img)
    result = model(img)

    result = result.data.numpy()

    print(f"This is {result[0]}!")


val('D:\Program\pytorch-project\data\catdog\train\cats\cats.1.jpg')