"""
Google Earth Engine Service Module
Handles satellite imagery acquisition and processing for land monitoring
Uses Sentinel-2 Harmonized and Landsat thermal data
"""

import ee
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import requests
from ..utils.logger import get_logger, log_gee_operation, log_error
from ..utils.config import settings

logger = get_logger(__name__)


class GEEService:
    """
    Service class for Google Earth Engine operations
    Provides satellite imagery and derived indices for land monitoring
    """
    
    def __init__(self):
        """Initialize GEE Service"""
        self.initialized = False
        self.project_id = settings.GEE_PROJECT_ID
        
    def initialize(self) -> bool:
        """
        Authenticate and initialize Earth Engine
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            Exception: If authentication or initialization fails
        """
        try:
            if self.initialized:
                logger.info("GEE already initialized")
                return True
            
            # Try service account authentication first
            if settings.GEE_SERVICE_ACCOUNT and settings.GEE_PRIVATE_KEY_PATH:
                logger.info("Authenticating with service account...")
                credentials = ee.ServiceAccountCredentials(
                    settings.GEE_SERVICE_ACCOUNT,
                    settings.GEE_PRIVATE_KEY_PATH
                )
                ee.Initialize(credentials, project=self.project_id)
            else:
                # Fall back to standard authentication
                logger.info("Authenticating with standard method...")
                ee.Authenticate()
                ee.Initialize(project=self.project_id)
            
            self.initialized = True
            logger.info("✓ Google Earth Engine initialized successfully")
            
            # Test with simple operation
            test_image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T000000_20200101T000000_T32TPS')
            test_info = test_image.getInfo()
            logger.debug(f"GEE connection test successful")
            
            return True
            
        except Exception as e:
            log_error(e, "GEE initialization")
            logger.error(f"Failed to initialize GEE: {str(e)}")
            self.initialized = False
            raise
    
    def _cloud_mask_sentinel2(self, image: ee.Image) -> ee.Image:
        """
        Apply cloud mask to Sentinel-2 image using QA60 band
        
        Args:
            image: Sentinel-2 image
            
        Returns:
            Cloud-masked image
        """
        qa = image.select('QA60')
        
        # Bits 10 and 11 are clouds and cirrus
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        
        # Both flags should be set to zero (clear conditions)
        mask = (
            qa.bitwiseAnd(cloud_bit_mask).eq(0)
            .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        )
        
        return image.updateMask(mask)
    
    def get_sentinel_composite(
        self,
        geojson_polygon: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get Sentinel-2 composite with RGB, NDVI, and NDBI
        
        Args:
            geojson_polygon: GeoJSON polygon defining area of interest
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary containing download URLs and metadata:
            {
                "rgb_url": str,
                "ndvi_url": str,
                "ndbi_url": str,
                "metadata": {
                    "scene_count": int,
                    "date_range": tuple,
                    "cloud_coverage": float
                }
            }
        """
        try:
            if not self.initialized:
                self.initialize()
            
            log_gee_operation("get_sentinel_composite", geojson_polygon)
            
            # Convert GeoJSON to EE Geometry
            geometry = ee.Geometry(geojson_polygon)
            
            # Load Sentinel-2 Harmonized Surface Reflectance
            sentinel = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            
            # Filter collection
            filtered = (
                sentinel
                .filterBounds(geometry)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', settings.SENTINEL_CLOUD_THRESHOLD))
                .map(self._cloud_mask_sentinel2)
            )
            
            # Get metadata
            scene_count = filtered.size().getInfo()
            logger.info(f"Found {scene_count} Sentinel-2 scenes")
            
            if scene_count == 0:
                logger.warning("No Sentinel-2 scenes found for given parameters")
                return {
                    "rgb_url": None,
                    "ndvi_url": None,
                    "ndbi_url": None,
                    "metadata": {
                        "scene_count": 0,
                        "error": "No scenes available"
                    }
                }
            
            # Create median composite
            composite = filtered.median()
            
            # Scale reflectance values (divide by 10000)
            composite = composite.divide(10000)
            
            # Select and compute indices
            # RGB bands
            rgb = composite.select(['B4', 'B3', 'B2']).clip(geometry)
            
            # NDVI = (NIR - Red) / (NIR + Red) = (B8 - B4) / (B8 + B4)
            nir = composite.select('B8')
            red = composite.select('B4')
            ndvi = (
                nir.subtract(red)
                .divide(nir.add(red))
                .rename('NDVI')
                .clip(geometry)
            )
            
            # NDBI = (SWIR - NIR) / (SWIR + NIR) = (B11 - B8) / (B11 + B8)
            swir = composite.select('B11')
            ndbi = (
                swir.subtract(nir)
                .divide(swir.add(nir))
                .rename('NDBI')
                .clip(geometry)
            )
            
            # Generate download URLs
            rgb_vis_params = {
                'min': 0.0,
                'max': 0.3,
                'bands': ['B4', 'B3', 'B2'],
                'dimensions': 1024,
                'region': geometry,
                'format': 'GEO_TIFF'
            }
            
            ndvi_vis_params = {
                'min': -1,
                'max': 1,
                'palette': ['red', 'yellow', 'green'],
                'dimensions': 1024,
                'region': geometry,
                'format': 'GEO_TIFF'
            }
            
            ndbi_vis_params = {
                'min': -1,
                'max': 1,
                'palette': ['blue', 'white', 'red'],
                'dimensions': 1024,
                'region': geometry,
                'format': 'GEO_TIFF'
            }
            
            # Get download URLs
            rgb_url = rgb.getDownloadURL(rgb_vis_params)
            ndvi_url = ndvi.getDownloadURL(ndvi_vis_params)
            ndbi_url = ndbi.getDownloadURL(ndbi_vis_params)
            
            # Calculate average cloud coverage
            avg_cloud = filtered.aggregate_mean('CLOUDY_PIXEL_PERCENTAGE').getInfo()
            
            logger.info(f"✓ Sentinel composite generated successfully")
            
            return {
                "rgb_url": rgb_url,
                "ndvi_url": ndvi_url,
                "ndbi_url": ndbi_url,
                "metadata": {
                    "scene_count": scene_count,
                    "date_range": (start_date, end_date),
                    "cloud_coverage": avg_cloud,
                    "scale": settings.SENTINEL_SCALE,
                    "crs": "EPSG:4326"
                }
            }
            
        except Exception as e:
            log_error(e, "get_sentinel_composite")
            raise
    
    def get_thermal_data(
        self,
        geojson_polygon: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get Landsat thermal data and convert to brightness temperature
        
        Args:
            geojson_polygon: GeoJSON polygon defining area of interest
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary containing thermal data URL and metadata
        """
        try:
            if not self.initialized:
                self.initialize()
            
            log_gee_operation("get_thermal_data", geojson_polygon)
            
            # Convert GeoJSON to EE Geometry
            geometry = ee.Geometry(geojson_polygon)
            
            # Load Landsat 8 Collection 2 Tier 1
            landsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            
            # Load Landsat 9 Collection 2 Tier 1
            landsat9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
            
            # Merge collections
            landsat = landsat8.merge(landsat9)
            
            # Filter collection
            filtered = (
                landsat
                .filterBounds(geometry)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt('CLOUD_COVER', 30))
            )
            
            scene_count = filtered.size().getInfo()
            logger.info(f"Found {scene_count} Landsat scenes")
            
            if scene_count == 0:
                logger.warning("No Landsat scenes found for given parameters")
                return {
                    "thermal_url": None,
                    "metadata": {
                        "scene_count": 0,
                        "error": "No scenes available"
                    }
                }
            
            # Create median composite
            composite = filtered.median()
            
            # Extract thermal band (ST_B10 for Collection 2)
            # Scale factor is 0.00341802, offset is 149.0
            thermal = composite.select('ST_B10').multiply(0.00341802).add(149.0)
            
            # Convert to Celsius
            thermal_celsius = thermal.subtract(273.15).rename('Temperature')
            
            # Clip to geometry
            thermal_clipped = thermal_celsius.clip(geometry)
            
            # Visualization parameters
            thermal_vis_params = {
                'min': 10,
                'max': 50,
                'palette': ['blue', 'cyan', 'yellow', 'red'],
                'dimensions': 1024,
                'region': geometry,
                'format': 'GEO_TIFF'
            }
            
            # Get download URL
            thermal_url = thermal_clipped.getDownloadURL(thermal_vis_params)
            
            # Calculate statistics
            stats = thermal_clipped.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.minMax(), '', True
                ).combine(
                    ee.Reducer.stdDev(), '', True
                ),
                geometry=geometry,
                scale=settings.LANDSAT_SCALE,
                maxPixels=1e9
            ).getInfo()
            
            logger.info(f"✓ Thermal data generated successfully")
            
            return {
                "thermal_url": thermal_url,
                "metadata": {
                    "scene_count": scene_count,
                    "date_range": (start_date, end_date),
                    "scale": settings.LANDSAT_SCALE,
                    "statistics": stats,
                    "units": "Celsius"
                }
            }
            
        except Exception as e:
            log_error(e, "get_thermal_data")
            raise
    
    def get_change_detection_images(
        self,
        geojson_polygon: Dict[str, Any],
        date_t1: str,
        date_t2: str,
        window_days: int = 30
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Get two comparative images for change detection
        
        Args:
            geojson_polygon: GeoJSON polygon
            date_t1: First date (before)
            date_t2: Second date (after)
            window_days: Days window around each date
            
        Returns:
            Tuple of (image_t1_url, image_t2_url)
        """
        try:
            if not self.initialized:
                self.initialize()
            
            geometry = ee.Geometry(geojson_polygon)
            
            # Helper function to get composite for a specific period
            def get_composite_for_period(center_date: str, days: int):
                date_obj = datetime.strptime(center_date, '%Y-%m-%d')
                from datetime import timedelta
                start = (date_obj - timedelta(days=days)).strftime('%Y-%m-%d')
                end = (date_obj + timedelta(days=days)).strftime('%Y-%m-%d')
                
                sentinel = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                filtered = (
                    sentinel
                    .filterBounds(geometry)
                    .filterDate(start, end)
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', settings.SENTINEL_CLOUD_THRESHOLD))
                    .map(self._cloud_mask_sentinel2)
                )
                
                return filtered.median().divide(10000).select(['B4', 'B3', 'B2']).clip(geometry)
            
            # Get composites
            image_t1 = get_composite_for_period(date_t1, window_days)
            image_t2 = get_composite_for_period(date_t2, window_days)
            
            vis_params = {
                'min': 0.0,
                'max': 0.3,
                'bands': ['B4', 'B3', 'B2'],
                'dimensions': 512,
                'region': geometry,
                'format': 'GEO_TIFF'
            }
            
            url_t1 = image_t1.getDownloadURL(vis_params)
            url_t2 = image_t2.getDownloadURL(vis_params)
            
            logger.info(f"✓ Change detection images generated")
            
            return (url_t1, url_t2)
            
        except Exception as e:
            log_error(e, "get_change_detection_images")
            return (None, None)


# Singleton instance
_gee_service_instance = None


def get_gee_service() -> GEEService:
    """
    Get or create GEE service singleton instance
    
    Returns:
        GEEService instance
    """
    global _gee_service_instance
    if _gee_service_instance is None:
        _gee_service_instance = GEEService()
    return _gee_service_instance


if __name__ == "__main__":
    # Test GEE service
    service = GEEService()
    service.initialize()
    
    # Test polygon (small area in Chhattisgarh)
    test_polygon = {
        "type": "Polygon",
        "coordinates": [[
            [81.6, 21.25],
            [81.7, 21.25],
            [81.7, 21.35],
            [81.6, 21.35],
            [81.6, 21.25]
        ]]
    }
    
    print("Testing Sentinel-2 composite...")
    result = service.get_sentinel_composite(
        test_polygon,
        "2023-01-01",
        "2023-03-31"
    )
    print(f"Scene count: {result['metadata']['scene_count']}")
