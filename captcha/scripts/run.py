import os
import torch
import torch.nn as nn

from captcha.data_processing.data_split import split_dataset
from captcha.data_processing.custom_dataset import load_data, get_custom_transform
from captcha.model.save_param import save_param

from captcha.model.resnet_based import CaptchaResNet
from captcha.model.vit_based import CaptchaViT
from captcha.model.deit_based import CaptchaDeiT

from captcha.scripts.eval import visualize_and_save_predictions, evaluate_model, load_model

def run_training_loop(args):
    transform = get_custom_transform()
    train_loader, val_loader, test_loader = load_data(args.splited_dir, transform, args.batch_size, args.max_dataset_size)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # Example setup
    characters = '0123456789abcdefghijklmnopqrstuvwxyz'
    
    num_classes = len('0123456789abcdefghijklmnopqrstuvwxyz')  # Adjust as necessary
    sequence_length = 5  # Adjust based on your CAPTCHA length
    if args.model == 0:
        model_name = "resnet18"
        model = CaptchaResNet(num_classes, sequence_length)

    elif args.model == 1:
        model_name = "vit_base_patch16_224"
        model = CaptchaViT(num_classes, sequence_length)
    elif args.model == 2:
        model_name = "deit_base_patch16_224"
        model = CaptchaDeiT(num_classes, sequence_length)
    
    print(f"model_selected: {model_name}")

    model.to(device)
    # Loss Function and Optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    if args.eval == 0:
        # Assuming 'model' is already defined and modified for the correct output
        model.train()
        for epoch in range(args.num_epochs):
            for images, labels in train_loader:
                images, labels = images.to(device), labels.to(device)
                # Assuming labels are now [batch_size, sequence_length] with class indices
                outputs = model(images)  # outputs should be [batch_size, sequence_length, num_classes]
                loss = 0
                for i in range(sequence_length):  # Loop over each character position
                    loss += criterion(outputs[:, i, :], labels[:, i])
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            print(f'Epoch [{epoch+1}/{args.num_epochs}], Loss: {loss.item():.4f}')

            if (epoch + 1) % 10 == 0:
                # Save the model
                if not os.path.exists(args.weights_dir): 
                    os.makedirs(args.weights_dir)
                save_param(epoch, model_name,model.state_dict(), args.weights_dir)

        evaluate_model(model, val_loader, device, characters)
    else:
        model = load_model(model, args.load_model, device)
        visualize_and_save_predictions(model, test_loader, device, characters, args.weights_dir)
        evaluate_model(model, test_loader, device, characters)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    
    # Directory path
    parser.add_argument("--original_dir", type=str, default="./captcha/data/samples")
    parser.add_argument("--splited_dir", type=str, default="./captcha/data/dataset")
    parser.add_argument("--weights_dir", type=str, default="./weights")
    parser.add_argument("--load_model", type=str, default="./weights/vit_base_patch16_224_23_11_39_89.pth")
    parser.add_argument("--eval", type=int, default=0) # 0: Resnet, # 1: VIT, # 2: DeIT

    # Hyperparam
    parser.add_argument("--model", type=int, default=0)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--max_dataset_size", type=int, default=850)
    parser.add_argument("--learning_rate", type=float, default=0.001)
    parser.add_argument("--num_epochs", type=int, default=10)

    args = parser.parse_args()

    split_dataset(args.original_dir, args.splited_dir)
    
    run_training_loop(args)

if __name__ == "__main__":
    main()
    
