import torch
import torch.nn as nn
from torchvision import models

class CaptchaResNet(nn.Module):
    def __init__(self, num_classes, sequence_length):
        super().__init__()
        self.num_classes = num_classes
        self.sequence_length = sequence_length
        base_model = models.resnet18(pretrained=True)
        num_features = base_model.fc.in_features
        base_model.fc = nn.Identity()  # Remove the original fully connected layer

        self.base_model = base_model
        self.fc = nn.Linear(num_features, num_classes * sequence_length)

    def forward(self, x):
        x = self.base_model(x)
        x = self.fc(x)
        # Reshape to have the correct output dimensions
        x = x.view(-1, self.sequence_length, self.num_classes)
        return x