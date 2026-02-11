"""
U-Net Architecture for Built-up Area Segmentation
Segments satellite imagery to detect built-up structures
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class DoubleConv(nn.Module):
    """
    Double Convolution block: (Conv2d -> BatchNorm -> ReLU) x 2
    """
    def __init__(self, in_channels: int, out_channels: int):
        super(DoubleConv, self).__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x):
        return self.double_conv(x)


class Down(nn.Module):
    """
    Downscaling with maxpool then double conv
    """
    def __init__(self, in_channels: int, out_channels: int):
        super(Down, self).__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels)
        )
    
    def forward(self, x):
        return self.maxpool_conv(x)


class Up(nn.Module):
    """
    Upscaling then double conv
    """
    def __init__(self, in_channels: int, out_channels: int, bilinear: bool = True):
        super(Up, self).__init__()
        
        # Use bilinear upsampling or transposed convolution
        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels)
        else:
            self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
            self.conv = DoubleConv(in_channels, out_channels)
    
    def forward(self, x1, x2):
        """
        x1: upsampled features
        x2: skip connection features from encoder
        """
        x1 = self.up(x1)
        
        # Handle size mismatch between x1 and x2
        diffY = x2.size()[2] - x1.size()[2]
        diffX = x2.size()[3] - x1.size()[3]
        
        x1 = F.pad(x1, [diffX // 2, diffX - diffX // 2,
                        diffY // 2, diffY - diffY // 2])
        
        # Concatenate skip connection
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)


class OutConv(nn.Module):
    """
    Output convolution layer
    """
    def __init__(self, in_channels: int, out_channels: int):
        super(OutConv, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)
    
    def forward(self, x):
        return self.conv(x)


class UNet(nn.Module):
    """
    U-Net: Convolutional Networks for Biomedical Image Segmentation
    https://arxiv.org/abs/1505.04597
    
    Adapted for satellite imagery built-up area detection
    
    Input: 3-channel RGB satellite image (B, 3, H, W)
    Output: 1-channel segmentation mask (B, 1, H, W) with values in [0, 1]
    """
    
    def __init__(
        self,
        n_channels: int = 3,
        n_classes: int = 1,
        bilinear: bool = True,
        base_features: int = 64
    ):
        """
        Initialize U-Net
        
        Args:
            n_channels: Number of input channels (3 for RGB)
            n_classes: Number of output classes (1 for binary segmentation)
            bilinear: Use bilinear upsampling (True) or transposed conv (False)
            base_features: Number of features in first layer (default: 64)
        """
        super(UNet, self).__init__()
        self.n_channels = n_channels
        self.n_classes = n_classes
        self.bilinear = bilinear
        
        # Encoder (Contracting Path)
        self.inc = DoubleConv(n_channels, base_features)
        self.down1 = Down(base_features, base_features * 2)
        self.down2 = Down(base_features * 2, base_features * 4)
        self.down3 = Down(base_features * 4, base_features * 8)
        
        # Bottleneck
        factor = 2 if bilinear else 1
        self.down4 = Down(base_features * 8, base_features * 16 // factor)
        
        # Decoder (Expanding Path)
        self.up1 = Up(base_features * 16, base_features * 8 // factor, bilinear)
        self.up2 = Up(base_features * 8, base_features * 4 // factor, bilinear)
        self.up3 = Up(base_features * 4, base_features * 2 // factor, bilinear)
        self.up4 = Up(base_features * 2, base_features, bilinear)
        
        # Output layer
        self.outc = OutConv(base_features, n_classes)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """
        Initialize model weights using He initialization
        """
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x: Input tensor of shape (B, C, H, W)
            
        Returns:
            Output segmentation mask of shape (B, 1, H, W)
        """
        # Encoder with skip connections
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)
        
        # Decoder with skip connections
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        
        # Output
        logits = self.outc(x)
        
        # Apply sigmoid for binary segmentation
        output = torch.sigmoid(logits)
        
        return output
    
    def predict(
        self,
        x: torch.Tensor,
        threshold: float = 0.5
    ) -> torch.Tensor:
        """
        Predict binary mask with threshold
        
        Args:
            x: Input tensor
            threshold: Classification threshold (default: 0.5)
            
        Returns:
            Binary mask (0 or 1)
        """
        self.eval()
        with torch.no_grad():
            output = self.forward(x)
            binary_mask = (output > threshold).float()
        return binary_mask
    
    def get_feature_maps(self, x: torch.Tensor) -> dict:
        """
        Extract intermediate feature maps for visualization
        
        Args:
            x: Input tensor
            
        Returns:
            Dictionary of feature maps at different scales
        """
        self.eval()
        with torch.no_grad():
            x1 = self.inc(x)
            x2 = self.down1(x1)
            x3 = self.down2(x2)
            x4 = self.down3(x3)
            x5 = self.down4(x4)
            
            return {
                'level1': x1,
                'level2': x2,
                'level3': x3,
                'level4': x4,
                'bottleneck': x5
            }


def create_unet(
    pretrained_path: str = None,
    device: str = 'cpu'
) -> UNet:
    """
    Create U-Net model with optional pretrained weights
    
    Args:
        pretrained_path: Path to pretrained weights
        device: Device to load model on ('cpu' or 'cuda')
        
    Returns:
        UNet model
    """
    model = UNet(n_channels=3, n_classes=1, bilinear=True)
    
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
    # Test U-Net architecture
    print("Testing U-Net architecture...")
    
    model = UNet(n_channels=3, n_classes=1)
    
    # Test input (batch_size=2, channels=3, height=256, width=256)
    test_input = torch.randn(2, 3, 256, 256)
    
    print(f"Input shape: {test_input.shape}")
    
    # Forward pass
    output = model(test_input)
    print(f"Output shape: {output.shape}")
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    
    print("✓ U-Net test successful")
