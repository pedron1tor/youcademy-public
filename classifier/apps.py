from django.apps import AppConfig
import torch
import torch.nn as nn
from django.conf import settings
import os


# Adjust the import based on your project structure
class LexilePredictor(nn.Module):

  def __init__(self, input_size, num_classes=7):
    super(LexilePredictor, self).__init__()
    self.fc1 = nn.Linear(input_size, 512)
    self.dropout1 = nn.Dropout(0.5)
    self.fc2 = nn.Linear(512, 256)
    self.dropout2 = nn.Dropout(0.5)
    self.fc3 = nn.Linear(256, num_classes)

  def forward(self, x):
    x = torch.relu(self.fc1(x))
    x = self.dropout1(x)
    x = torch.relu(self.fc2(x))
    x = self.dropout2(x)
    x = self.fc3(x)
    return torch.softmax(x, dim=1)


class ClassifierConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "classifier"
  verbose_name = "Classifier"

  def ready(self):
    if not hasattr(self, 'model'):
      model_path = os.path.join(settings.BASE_DIR, 'classifier',
                                'lexile_predictor_model.pth')
      self.model = LexilePredictor(input_size=4000, num_classes=7)
      self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
      self.model.eval()
      print("Model loaded and ready!")
