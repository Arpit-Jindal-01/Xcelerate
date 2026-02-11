"""
CSIDC Portal Integration Service
Handles data fetching and integration from Chhattisgarh State Industrial Development Corporation Portal
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

from ..utils.logger import get_logger, log_error, log_api_request
from ..utils.config import settings

logger = get_logger(__name__)


class CSIDCPortalService:
    """
    Service class for CSIDC Portal operations
    Provides integration with CSIDC geoportal for area data fetching
    """
    
    def __init__(self):
        """Initialize CSIDC Portal Service"""
        self.base_url = "https://cggis.cgstate.gov.in/csidc"
        self.session: Optional[aiohttp.ClientSession] = None
        self.area_types = {
            "industrial_areas": "Industrial Areas",
            "land_bank": "Land Bank Areas", 
            "old_industrial": "Old Industrial Areas",
            "directorate_industrial": "Directorate Industrial Areas",
            "amenities": "Amenities"
        }
        
        # Map layer identifiers from the portal
        self.layer_configs = {
            "industrial_areas": {"layer_id": "industrial", "color": "#FF6B6B"},
            "land_bank": {"layer_id": "landbank", "color": "#4ECDC4"},
            "old_industrial": {"layer_id": "old_industrial", "color": "#45B7D1"},
            "directorate_industrial": {"layer_id": "directorate", "color": "#96CEB4"},
            "amenities": {"layer_id": "amenities", "color": "#FFEAA7"}
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'CSIDC-Monitoring-System/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_area_data(self, area_type: str, bbox: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Fetch area data from CSIDC portal
        
        Args:
            area_type: Type of area ('industrial_areas', 'land_bank', etc.)
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            
        Returns:
            Dictionary containing GeoJSON data and metadata
        """
        try:
            if area_type not in self.area_types:
                raise ValueError(f"Invalid area type: {area_type}")
            
            logger.info(f"Fetching {area_type} data from CSIDC portal")
            
            # Construct API endpoint (assuming WFS/WMS services)
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typename": f"csidc:{self.layer_configs[area_type]['layer_id']}",
                "outputFormat": "application/json",
                "srsname": "EPSG:4326"
            }
            
            if bbox:
                params["bbox"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326"
            
            # Try WFS endpoint first
            wfs_url = f"{self.base_url}/geoserver/csidc/wfs"
            
            async with self.session.get(wfs_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully fetched {len(data.get('features', []))} features for {area_type}")
                    return {
                        "type": "FeatureCollection",
                        "features": data.get('features', []),
                        "metadata": {
                            "area_type": area_type,
                            "source": "CSIDC Portal",
                            "timestamp": datetime.now().isoformat(),
                            "count": len(data.get('features', [])),
                            "bbox": bbox
                        }
                    }
                else:
                    logger.warning(f"WFS request failed with status {response.status}, trying alternative method")
                    return await self._fetch_alternative_data(area_type, bbox)
                    
        except Exception as e:
            log_error(e, f"fetch_area_data_{area_type}")
            return await self._fetch_alternative_data(area_type, bbox)
    
    async def _fetch_alternative_data(self, area_type: str, bbox: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Alternative data fetching method when WFS is not available
        Attempts to parse the portal's JavaScript or API responses
        """
        try:
            # Try to fetch the main portal page and extract data
            portal_url = f"{self.base_url}/"
            
            async with self.session.get(portal_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Look for embedded JSON data or API endpoints
                    json_pattern = r'var\s+' + area_type + r'Data\s*=\s*({.*?});'
                    match = re.search(json_pattern, html_content, re.DOTALL)
                    
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            return self._process_extracted_data(data, area_type, bbox)
                        except json.JSONDecodeError:
                            pass
                    
                    # If no embedded data found, create mock data structure
                    logger.warning(f"No data found for {area_type}, creating placeholder structure")
                    return self._create_placeholder_data(area_type, bbox)
                    
        except Exception as e:
            log_error(e, f"_fetch_alternative_data_{area_type}")
            return self._create_placeholder_data(area_type, bbox)
    
    def _create_placeholder_data(self, area_type: str, bbox: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Create placeholder data structure for area types
        This is used when actual data cannot be fetched from the portal
        """
        # Create sample features based on Chhattisgarh state bounds
        cg_bounds = [80.2, 19.0, 84.4, 24.1]  # Approximate Chhattisgarh bounds
        
        if not bbox:
            bbox = cg_bounds
            
        # Generate sample features for demonstration
        features = []
        if area_type == "industrial_areas":
            features = self._generate_sample_industrial_areas(bbox)
        elif area_type == "land_bank":
            features = self._generate_sample_land_bank(bbox)
        elif area_type == "amenities":
            features = self._generate_sample_amenities(bbox)
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "area_type": area_type,
                "source": "CSIDC Portal (Placeholder)",
                "timestamp": datetime.now().isoformat(),
                "count": len(features),
                "bbox": bbox,
                "note": "This is placeholder data. Actual integration requires API access."
            }
        }
    
    def _generate_sample_industrial_areas(self, bbox: List[float]) -> List[Dict]:
        """Generate sample industrial area features"""
        return [
            {
                "type": "Feature",
                "properties": {
                    "name": "Raipur Industrial Area",
                    "area_type": "industrial",
                    "status": "operational",
                    "size_hectares": 1250.5,
                    "district": "Raipur",
                    "established": "1985"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [81.63, 21.25], [81.68, 21.25], 
                        [81.68, 21.20], [81.63, 21.20], [81.63, 21.25]
                    ]]
                }
            },
            {
                "type": "Feature", 
                "properties": {
                    "name": "Bhilai Industrial Complex",
                    "area_type": "industrial",
                    "status": "operational",
                    "size_hectares": 2100.8,
                    "district": "Durg",
                    "established": "1955"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [81.35, 21.20], [81.42, 21.20],
                        [81.42, 21.15], [81.35, 21.15], [81.35, 21.20]
                    ]]
                }
            }
        ]
    
    def _generate_sample_land_bank(self, bbox: List[float]) -> List[Dict]:
        """Generate sample land bank features"""
        return [
            {
                "type": "Feature",
                "properties": {
                    "name": "Korba Land Bank",
                    "area_type": "land_bank", 
                    "status": "available",
                    "size_hectares": 850.2,
                    "district": "Korba",
                    "purpose": "Future Industrial Development"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [82.65, 22.35], [82.72, 22.35],
                        [82.72, 22.30], [82.65, 22.30], [82.65, 22.35]
                    ]]
                }
            }
        ]
    
    def _generate_sample_amenities(self, bbox: List[float]) -> List[Dict]:
        """Generate sample amenity features"""
        return [
            {
                "type": "Feature",
                "properties": {
                    "name": "Industrial Training Institute",
                    "amenity_type": "education",
                    "status": "operational",
                    "serves_areas": ["Raipur Industrial Area"]
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [81.65, 21.23]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "name": "Power Sub-station",
                    "amenity_type": "infrastructure",
                    "status": "operational",
                    "capacity": "220 KV"
                },
                "geometry": {
                    "type": "Point", 
                    "coordinates": [81.67, 21.22]
                }
            }
        ]
    
    async def get_available_layers(self) -> Dict[str, Any]:
        """
        Get available layers from CSIDC portal
        
        Returns:
            Dictionary of available layers and their metadata
        """
        try:
            capabilities_url = f"{self.base_url}/geoserver/csidc/wms"
            params = {
                "service": "WMS",
                "version": "1.3.0", 
                "request": "GetCapabilities"
            }
            
            async with self.session.get(capabilities_url, params=params) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    return self._parse_capabilities(xml_content)
                    
        except Exception as e:
            log_error(e, "get_available_layers")
            
        # Return default layer configuration
        return {
            "layers": self.layer_configs,
            "area_types": self.area_types,
            "base_url": self.base_url
        }
    
    def _parse_capabilities(self, xml_content: str) -> Dict[str, Any]:
        """Parse WMS GetCapabilities response"""
        try:
            root = ET.fromstring(xml_content)
            layers = {}
            
            # Extract layer information from XML
            for layer in root.iter():
                if layer.tag.endswith('Layer') and layer.find('.//Name') is not None:
                    name = layer.find('.//Name').text
                    title = layer.find('.//Title')
                    title_text = title.text if title is not None else name
                    
                    layers[name] = {
                        "name": name,
                        "title": title_text,
                        "available": True
                    }
            
            return {
                "layers": layers,
                "area_types": self.area_types,
                "base_url": self.base_url,
                "parsed_from": "WMS Capabilities"
            }
            
        except ET.ParseError:
            return self.get_available_layers()
    
    async def search_areas(self, query: str, area_type: Optional[str] = None) -> List[Dict]:
        """
        Search for areas by name or properties
        
        Args:
            query: Search query string
            area_type: Optional area type filter
            
        Returns:
            List of matching features
        """
        try:
            all_results = []
            
            # Search across all area types or specific type
            search_types = [area_type] if area_type else list(self.area_types.keys())
            
            for atype in search_types:
                data = await self.fetch_area_data(atype)
                features = data.get('features', [])
                
                # Filter features by query
                for feature in features:
                    props = feature.get('properties', {})
                    if any(query.lower() in str(value).lower() for value in props.values()):
                        feature['area_type'] = atype
                        all_results.append(feature)
            
            logger.info(f"Search '{query}' returned {len(all_results)} results")
            return all_results
            
        except Exception as e:
            log_error(e, f"search_areas_{query}")
            return []
    
    async def get_area_statistics(self) -> Dict[str, Any]:
        """
        Get statistics for all area types
        
        Returns:
            Dictionary containing area statistics
        """
        try:
            stats = {}
            
            for area_type in self.area_types.keys():
                data = await self.fetch_area_data(area_type)
                features = data.get('features', [])
                
                # Calculate basic statistics
                total_count = len(features)
                total_area = 0
                
                for feature in features:
                    props = feature.get('properties', {})
                    if 'size_hectares' in props:
                        total_area += float(props['size_hectares'])
                
                stats[area_type] = {
                    "count": total_count,
                    "total_area_hectares": total_area,
                    "type_name": self.area_types[area_type]
                }
            
            stats["summary"] = {
                "total_areas": sum(s["count"] for s in stats.values()),
                "total_area_hectares": sum(s["total_area_hectares"] for s in stats.values()),
                "last_updated": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            log_error(e, "get_area_statistics")
            return {}


# Dependency injection function
async def get_csidc_service() -> CSIDCPortalService:
    """Dependency injection for CSIDC Portal Service"""
    service = CSIDCPortalService()
    return service