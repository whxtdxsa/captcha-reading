import os
import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

from captcha.data_processing.data_split import get_file_names

# Dataset and DataLoader
class CaptchaDataset(Dataset):
    def __init__(self, img_dir, max_dataset_size, transform=None):
        self.img_dir = img_dir
        self.transform = transform
        self.image_files = get_file_names(img_dir)[:max_dataset_size]
        self.characters = '0123456789abcdefghijklmnopqrstuvwxyz'  # Include both digits and letters
        self.char_to_int = {char: idx for idx, char in enumerate(self.characters)}
   
    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        img_name = self.image_files[idx]
        img_path = os.path.join(self.img_dir, img_name)
        img = Image.open(img_path).convert('RGB')

        if self.transform:
            img = self.transform(img)
        
        # Extracting and encoding labels
        label = img_name.split('.')[0]  # Assuming label is before an underscore
        label_encoded = torch.zeros(len(label), len(self.characters))
        for i, char in enumerate(label):
            position = self.char_to_int[char]
            label_encoded[i][position] = 1  # One-hot encode each character position

        return img, label_encoded
    
def load_data(dataset_dir, transform, batch_size, max_dataset_size):
    # Creating dataset and data loader instances
    train_dataset = CaptchaDataset(dataset_dir + "/train", max_dataset_size, transform=transform)
    val_dataset = CaptchaDataset(dataset_dir + "/val", max_dataset_size, transform=transform)
    test_dataset = CaptchaDataset(dataset_dir + "/test", max_dataset_size, transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=4, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=4, pin_memory=True)
    return train_loader, val_loader, test_loader

# Function to calculate padding
def get_padding(image):
    width, height = image.size
    if width > height:
        padding = (0, (width - height) // 2, 0, (width - height) - (width - height) // 2)
    else:
        padding = ((height - width) // 2, 0, (height - width) - (height - width) // 2, 0)
    return padding

# Custom transform to add padding
class PadToSquare(object):
    def __call__(self, image):
        padding = get_padding(image)
        return transforms.functional.pad(image, padding, fill=0, padding_mode='constant')
    
def get_custom_transform():
    transform = transforms.Compose([
        PadToSquare(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        # transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return transform
