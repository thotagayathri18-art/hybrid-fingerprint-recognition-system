import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image

# Same CNN structure as training
class FingerprintCNN(nn.Module):
    def __init__(self, num_classes):
        super(FingerprintCNN, self).__init__()

        self.model = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Flatten(),
            nn.Linear(32 * 32 * 32, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        return self.model(x)

# Classes from training
classes = ['person1', 'person2', 'person3']

# Load model
model = FingerprintCNN(num_classes=len(classes))
model.load_state_dict(torch.load("fingerprint_cnn.pth"))
model.eval()

# Image transform
transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((128,128)),
    transforms.ToTensor()
])

# Test image path
image_path = "database/finger1.BMP"  # change if needed

# Load image
image = Image.open(image_path)
image = transform(image).unsqueeze(0)

# Predict
with torch.no_grad():
    outputs = model(image)
    _, predicted = torch.max(outputs, 1)

predicted_class = classes[predicted.item()]

print("Predicted Person:", predicted_class)