"""
Siamese Convolutional Neural Network for Change Detection
Compares two temporal satellite images to detect changes
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class CNNBackbone(nn.Module):
    """
    Shared CNN backbone for feature extraction
    """
    def __init__(self, in_channels: int = 3):
        super(CNNBackbone, self).__init__()
        
        # Convolutional layers with progressive feature extraction
        self.conv1 = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        self.conv2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        self.conv3 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        self.conv4 = nn.Sequential(
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # Global average pooling
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extract features from input image
        
        Args:
            x: Input image tensor of shape (B, C, H, W)
            
        Returns:
            Feature vector of shape (B, 512)
        """
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)  # Flatten
        return x


class SiameseCNN(nn.Module):
    """
    Siamese CNN for temporal change detection
    
    Takes two images from different time periods and outputs a change probability score
    
    Architecture:
    1. Shared CNN backbone extracts features from both images
    2. Feature difference is computed
    3. Fully connected layers classify change probability
    """
    
    def __init__(
        self,
        in_channels: int = 3,
        feature_dim: int = 512,
        dropout: float = 0.5
    ):
        """
        Initialize Siamese CNN
        
        Args:
            in_channels: Number of input channels (3 for RGB)
            feature_dim: Dimension of feature vector from backbone
            dropout: Dropout rate for regularization
        """
        super(SiameseCNN, self).__init__()
        
        # Shared CNN backbone (weights shared between both branches)
        self.backbone = CNNBackbone(in_channels=in_channels)
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(feature_dim, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Sigmoid()  # Output probability [0, 1]
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """
        Initialize model weights using He initialization for conv layers
        and Xavier for linear layers
        """
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.constant_(m.bias, 0)
    
    def forward_once(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through one branch (shared backbone)
        
        Args:
            x: Input image tensor
            
        Returns:
            Feature vector
        """
        return self.backbone(x)
    
    def forward(
        self,
        x1: torch.Tensor,
        x2: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass through both branches
        
        Args:
            x1: First image (Time T1) of shape (B, C, H, W)
            x2: Second image (Time T2) of shape (B, C, H, W)
            
        Returns:
            Change probability score of shape (B, 1) with values in [0, 1]
        """
        # Extract features from both images using shared backbone
        features1 = self.forward_once(x1)
        features2 = self.forward_once(x2)
        
        # Compute absolute difference
        diff = torch.abs(features1 - features2)
        
        # Classify change probability
        change_score = self.classifier(diff)
        
        return change_score
    
    def predict(
        self,
        x1: torch.Tensor,
        x2: torch.Tensor,
        threshold: float = 0.5
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict change with threshold
        
        Args:
            x1: First image
            x2: Second image
            threshold: Classification threshold (default: 0.5)
            
        Returns:
            Tuple of (change_scores, binary_predictions)
        """
        self.eval()
        with torch.no_grad():
            change_scores = self.forward(x1, x2)
            binary_predictions = (change_scores > threshold).float()
        return change_scores, binary_predictions
    
    def get_feature_similarity(
        self,
        x1: torch.Tensor,
        x2: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute cosine similarity between feature vectors
        
        Args:
            x1: First image
            x2: Second image
            
        Returns:
            Cosine similarity scores
        """
        self.eval()
        with torch.no_grad():
            features1 = self.forward_once(x1)
            features2 = self.forward_once(x2)
            
            # Cosine similarity
            similarity = F.cosine_similarity(features1, features2, dim=1)
        
        return similarity
    
    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extract feature embeddings for visualization or analysis
        
        Args:
            x: Input image
            
        Returns:
            Feature vector
        """
        self.eval()
        with torch.no_grad():
            features = self.forward_once(x)
        return features


class ContrastiveLoss(nn.Module):
    """
    Contrastive loss for training Siamese networks
    Used when training with pairs of similar/dissimilar images
    """
    def __init__(self, margin: float = 1.0):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
    
    def forward(
        self,
        output1: torch.Tensor,
        output2: torch.Tensor,
        label: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute contrastive loss
        
        Args:
            output1: Features from first image
            output2: Features from second image
            label: 1 for similar, 0 for dissimilar
            
        Returns:
            Loss value
        """
        euclidean_distance = F.pairwise_distance(output1, output2)
        
        loss = torch.mean(
            (1 - label) * torch.pow(euclidean_distance, 2) +
            label * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2)
        )
        
        return loss


def create_siamese_cnn(
    pretrained_path: str = None,
    device: str = 'cpu'
) -> SiameseCNN:
    """
    Create Siamese CNN model with optional pretrained weights
    
    Args:
        pretrained_path: Path to pretrained weights
        device: Device to load model on ('cpu' or 'cuda')
        
    Returns:
        SiameseCNN model
    """
    model = SiameseCNN(in_channels=3, feature_dim=512, dropout=0.5)
    
    if pretrained_path:
        try:
            state_dict = torch.load(pretrained_path, map_location=device)
            model.load_state_dict(state_dict)
            print(f"✓ Loaded pretrained weights from {pretrained_path}")
        except Exception as e:
            print(f"⚠ Could not load pretrained weights: {str(e)}")
    
    model = model.to(device)
    model.eval()
    
    return model


if __name__ == "__main__":
    # Test Siamese CNN architecture
    print("Testing Siamese CNN architecture...")
    
    model = SiameseCNN(in_channels=3, feature_dim=512)
    
    # Test inputs (batch_size=2, channels=3, height=256, width=256)
    test_image_t1 = torch.randn(2, 3, 256, 256)
    test_image_t2 = torch.randn(2, 3, 256, 256)
    
    print(f"Input T1 shape: {test_image_t1.shape}")
    print(f"Input T2 shape: {test_image_t2.shape}")
    
    # Forward pass
    change_scores = model(test_image_t1, test_image_t2)
    print(f"Change scores shape: {change_scores.shape}")
    print(f"Change scores: {change_scores.squeeze().tolist()}")
    
    # Test prediction
    scores, predictions = model.predict(test_image_t1, test_image_t2, threshold=0.5)
    print(f"Binary predictions: {predictions.squeeze().tolist()}")
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    
    print("✓ Siamese CNN test successful")
