"""
Machine Learning Service Module
Handles inference for built-up detection, change detection, and thermal anomalies
"""

import torch
import numpy as np
import cv2
from PIL import Image
from typing import Optional, Tuple, Dict, Any
import os
from pathlib import Path
import time

from ..models.unet import UNet, create_unet
from ..models.siamese import SiameseCNN, create_siamese_cnn
from ..utils.logger import get_logger, log_ml_inference, log_error
from ..utils.config import settings

logger = get_logger(__name__)


class MLService:
    """
    Service class for machine learning inference operations
    Provides built-up detection, change detection, and thermal anomaly detection
    """
    
    def __init__(self):
        """Initialize ML Service"""
        self.device = torch.device(settings.ML_DEVICE if torch.cuda.is_available() else 'cpu')
        logger.info(f"ML Service initialized on device: {self.device}")
        
        # Model instances
        self.unet_model: Optional[UNet] = None
        self.siamese_model: Optional[SiameseCNN] = None
        
        # Model metadata
        self.unet_version = "v1.0"
        self.siamese_version = "v1.0"
        
        # Load models
        self._load_models()
    
    def _load_models(self):
        """Load pretrained models"""
        try:
            # Load U-Net for built-up detection
            unet_path = os.path.join(settings.ML_MODEL_PATH, settings.UNET_WEIGHTS)
            if os.path.exists(unet_path):
                self.unet_model = create_unet(unet_path, device=str(self.device))
                logger.info(f"✓ U-Net model loaded from {unet_path}")
            else:
                logger.warning(f"U-Net weights not found at {unet_path}, using untrained model")
                self.unet_model = create_unet(pretrained_path=None, device=str(self.device))
            
            # Load Siamese CNN for change detection
            siamese_path = os.path.join(settings.ML_MODEL_PATH, settings.SIAMESE_WEIGHTS)
            if os.path.exists(siamese_path):
                self.siamese_model = create_siamese_cnn(siamese_path, device=str(self.device))
                logger.info(f"✓ Siamese CNN model loaded from {siamese_path}")
            else:
                logger.warning(f"Siamese weights not found at {siamese_path}, using untrained model")
                self.siamese_model = create_siamese_cnn(pretrained_path=None, device=str(self.device))
            
        except Exception as e:
            log_error(e, "load_models")
            raise
    
    def _preprocess_image(
        self,
        image_path: str,
        target_size: Tuple[int, int] = (256, 256)
    ) -> torch.Tensor:
        """
        Preprocess image for model inference
        
        Args:
            image_path: Path to image file
            target_size: Target size (H, W)
            
        Returns:
            Preprocessed tensor of shape (1, C, H, W)
        """
        try:
            # Read image
            if image_path.startswith('http'):
                # Download from URL
                import requests
                from io import BytesIO
                response = requests.get(image_path, timeout=30)
                image = Image.open(BytesIO(response.content))
            else:
                image = Image.open(image_path)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize
            image = image.resize(target_size, Image.BILINEAR)
            
            # Convert to numpy array and normalize
            image_np = np.array(image).astype(np.float32) / 255.0
            
            # Convert to torch tensor (H, W, C) -> (C, H, W)
            image_tensor = torch.from_numpy(image_np).permute(2, 0, 1)
            
            # Add batch dimension (C, H, W) -> (1, C, H, W)
            image_tensor = image_tensor.unsqueeze(0)
            
            return image_tensor.to(self.device)
            
        except Exception as e:
            log_error(e, f"preprocess_image: {image_path}")
            raise
    
    def detect_builtup(
        self,
        image_path: str,
        threshold: float = 0.5,
        return_visualization: bool = False
    ) -> Dict[str, Any]:
        """
        Detect built-up areas in satellite image using U-Net
        
        Args:
            image_path: Path to RGB satellite image
            threshold: Classification threshold (0-1)
            return_visualization: Whether to return visualization
            
        Returns:
            Dictionary containing:
            - mask: Binary segmentation mask (numpy array)
            - builtup_area_pixels: Number of built-up pixels
            - total_pixels: Total number of pixels
            - builtup_percentage: Percentage of built-up area
            - confidence: Average confidence score
            - visualization: Optional visualization (if requested)
        """
        try:
            start_time = time.time()
            
            # Preprocess image
            image_tensor = self._preprocess_image(image_path)
            
            # Run inference
            self.unet_model.eval()
            with torch.no_grad():
                output = self.unet_model(image_tensor)
            
            # Get mask
            mask_prob = output.squeeze().cpu().numpy()
            mask_binary = (mask_prob > threshold).astype(np.uint8)
            
            # Calculate statistics
            total_pixels = mask_binary.size
            builtup_pixels = np.sum(mask_binary)
            builtup_percentage = (builtup_pixels / total_pixels) * 100
            avg_confidence = float(np.mean(mask_prob[mask_binary == 1])) if builtup_pixels > 0 else 0.0
            
            duration = time.time() - start_time
            log_ml_inference("U-Net", image_tensor.shape, duration)
            
            result = {
                "mask": mask_binary,
                "mask_prob": mask_prob,
                "builtup_area_pixels": int(builtup_pixels),
                "total_pixels": int(total_pixels),
                "builtup_percentage": float(builtup_percentage),
                "confidence": avg_confidence,
                "model_version": self.unet_version,
                "inference_time": duration
            }
            
            # Optional visualization
            if return_visualization:
                vis = self._create_segmentation_visualization(
                    image_tensor.squeeze().cpu().numpy(),
                    mask_prob
                )
                result["visualization"] = vis
            
            logger.info(f"✓ Built-up detection: {builtup_percentage:.2f}% built-up")
            
            return result
            
        except Exception as e:
            log_error(e, "detect_builtup")
            raise
    
    def detect_change(
        self,
        image_t1_path: str,
        image_t2_path: str,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Detect changes between two temporal images using Siamese CNN
        
        Args:
            image_t1_path: Path to first image (earlier time)
            image_t2_path: Path to second image (later time)
            threshold: Change detection threshold (0-1)
            
        Returns:
            Dictionary containing:
            - change_score: Change probability (0-1)
            - has_changed: Boolean indicator
            - confidence: Confidence level
        """
        try:
            start_time = time.time()
            
            # Preprocess both images
            image_t1 = self._preprocess_image(image_t1_path)
            image_t2 = self._preprocess_image(image_t2_path)
            
            # Run inference
            self.siamese_model.eval()
            with torch.no_grad():
                change_score = self.siamese_model(image_t1, image_t2)
            
            change_score_value = float(change_score.item())
            has_changed = change_score_value > threshold
            
            duration = time.time() - start_time
            log_ml_inference("Siamese CNN", image_t1.shape, duration)
            
            result = {
                "change_score": change_score_value,
                "has_changed": has_changed,
                "confidence": change_score_value if has_changed else (1 - change_score_value),
                "threshold_used": threshold,
                "model_version": self.siamese_version,
                "inference_time": duration
            }
            
            status = "CHANGED" if has_changed else "NO CHANGE"
            logger.info(f"✓ Change detection: {status} (score: {change_score_value:.3f})")
            
            return result
            
        except Exception as e:
            log_error(e, "detect_change")
            raise
    
    def detect_heat_anomaly(
        self,
        thermal_image_path: str,
        temperature_threshold: float = 35.0,
        anomaly_percentile: float = 90.0
    ) -> Dict[str, Any]:
        """
        Detect thermal anomalies indicating industrial activity
        
        Args:
            thermal_image_path: Path to thermal/temperature raster
            temperature_threshold: Absolute temperature threshold (Celsius)
            anomaly_percentile: Percentile for relative anomaly detection
            
        Returns:
            Dictionary containing:
            - heat_mask: Binary mask of heat anomalies
            - hot_area_pixels: Number of anomalous pixels
            - mean_temperature: Mean temperature
            - max_temperature: Maximum temperature
            - anomaly_percentage: Percentage of anomalous area
        """
        try:
            start_time = time.time()
            
            # Read thermal image (could be GeoTIFF)
            try:
                import rasterio
                with rasterio.open(thermal_image_path) as src:
                    thermal_data = src.read(1)  # Read first band
            except:
                # Fallback to regular image reading
                thermal_img = cv2.imread(thermal_image_path, cv2.IMREAD_GRAYSCALE)
                thermal_data = thermal_img.astype(np.float32)
            
            # Calculate statistics
            mean_temp = float(np.mean(thermal_data))
            max_temp = float(np.max(thermal_data))
            min_temp = float(np.min(thermal_data))
            
            # Detect anomalies using both absolute and relative thresholds
            absolute_mask = thermal_data > temperature_threshold
            
            percentile_threshold = np.percentile(thermal_data, anomaly_percentile)
            relative_mask = thermal_data > percentile_threshold
            
            # Combine masks (logical OR)
            heat_mask = (absolute_mask | relative_mask).astype(np.uint8)
            
            # Calculate statistics
            total_pixels = heat_mask.size
            hot_pixels = np.sum(heat_mask)
            anomaly_percentage = (hot_pixels / total_pixels) * 100
            
            duration = time.time() - start_time
            
            result = {
                "heat_mask": heat_mask,
                "hot_area_pixels": int(hot_pixels),
                "total_pixels": int(total_pixels),
                "anomaly_percentage": float(anomaly_percentage),
                "mean_temperature": mean_temp,
                "max_temperature": max_temp,
                "min_temperature": min_temp,
                "temperature_threshold": temperature_threshold,
                "percentile_threshold": float(percentile_threshold),
                "inference_time": duration
            }
            
            logger.info(
                f"✓ Heat anomaly detection: {anomaly_percentage:.2f}% anomalous "
                f"(mean: {mean_temp:.1f}°C, max: {max_temp:.1f}°C)"
            )
            
            return result
            
        except Exception as e:
            log_error(e, "detect_heat_anomaly")
            raise
    
    def _create_segmentation_visualization(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        alpha: float = 0.5
    ) -> np.ndarray:
        """
        Create visualization overlay of segmentation mask on image
        
        Args:
            image: Original image (C, H, W)
            mask: Segmentation mask (H, W)
            alpha: Overlay transparency
            
        Returns:
            Visualization image
        """
        # Convert image to HWC format
        if image.shape[0] == 3:
            image = np.transpose(image, (1, 2, 0))
        
        # Normalize image to 0-255
        image = (image * 255).astype(np.uint8)
        
        # Create colored mask (red for built-up)
        colored_mask = np.zeros_like(image)
        colored_mask[:, :, 0] = (mask * 255).astype(np.uint8)  # Red channel
        
        # Overlay
        visualization = cv2.addWeighted(image, 1 - alpha, colored_mask, alpha, 0)
        
        return visualization


# Singleton instance
_ml_service_instance = None


def get_ml_service() -> MLService:
    """
    Get or create ML service singleton instance
    
    Returns:
        MLService instance
    """
    global _ml_service_instance
    if _ml_service_instance is None:
        _ml_service_instance = MLService()
    return _ml_service_instance


if __name__ == "__main__":
    # Test ML service
    print("Testing ML Service...")
    
    service = MLService()
    print(f"Device: {service.device}")
    print(f"U-Net loaded: {service.unet_model is not None}")
    print(f"Siamese CNN loaded: {service.siamese_model is not None}")
    
    print("✓ ML Service test successful")
