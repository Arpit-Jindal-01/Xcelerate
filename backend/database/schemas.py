"""
Pydantic Schemas for API Request/Response Validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enumerations (matching database enums)
class ViolationType(str, Enum):
    ENCROACHMENT = "encroachment"
    ILLEGAL_CONSTRUCTION = "illegal_construction"
    UNUSED_LAND = "unused_land"
    SUSPICIOUS_CHANGE = "suspicious_change"
    COMPLIANT = "compliant"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LandUseType(str, Enum):
    INDUSTRIAL = "industrial"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"
    WAREHOUSE = "warehouse"
    MANUFACTURING = "manufacturing"
    LOGISTICS = "logistics"


class CSIDCAreaType(str, Enum):
    INDUSTRIAL_AREA = "industrial_area"
    LAND_BANK = "land_bank"
    OLD_INDUSTRIAL = "old_industrial"
    DIRECTORATE_INDUSTRIAL = "directorate_industrial"
    AMENITY = "amenity"


class AreaStatus(str, Enum):
    OPERATIONAL = "operational"
    AVAILABLE = "available"
    UNDER_DEVELOPMENT = "under_development"
    PLANNED = "planned"
    CLOSED = "closed"


class AmenityType(str, Enum):
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    INFRASTRUCTURE = "infrastructure"
    TRANSPORTATION = "transportation"
    UTILITIES = "utilities"
    FINANCE = "finance"
    RECREATION = "recreation"


# Base Schemas
class GeoJSONGeometry(BaseModel):
    """GeoJSON Geometry schema"""
    type: str
    coordinates: List[Any]


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature schema"""
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: Dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection schema"""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


# Plot Schemas
class PlotBase(BaseModel):
    """Base plot schema"""
    plot_id: str
    approved_area: float = Field(..., gt=0, description="Approved area in square meters")
    approved_land_use: LandUseType
    industry_type: Optional[str] = None
    industry_name: Optional[str] = None
    owner_name: Optional[str] = None
    owner_contact: Optional[str] = None


class PlotCreate(PlotBase):
    """Schema for creating a new plot"""
    geometry: GeoJSONGeometry
    allotment_date: Optional[datetime] = None
    lease_expiry: Optional[datetime] = None


class PlotUpdate(BaseModel):
    """Schema for updating a plot"""
    approved_area: Optional[float] = None
    approved_land_use: Optional[LandUseType] = None
    industry_type: Optional[str] = None
    industry_name: Optional[str] = None
    owner_name: Optional[str] = None
    is_active: Optional[bool] = None


class PlotResponse(PlotBase):
    """Schema for plot response"""
    geometry: GeoJSONGeometry
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Detection Schemas
class DetectionBase(BaseModel):
    """Base detection schema"""
    plot_id: str
    built_up_area: Optional[float] = None
    heat_signature_area: Optional[float] = None
    change_score: Optional[float] = Field(None, ge=0, le=1)
    vegetation_index: Optional[float] = None
    built_up_index: Optional[float] = None


class DetectionCreate(DetectionBase):
    """Schema for creating detection record"""
    detected_geometry: Optional[GeoJSONGeometry] = None
    sentinel_date: Optional[datetime] = None
    landsat_date: Optional[datetime] = None
    model_version_unet: Optional[str] = None
    model_version_siamese: Optional[str] = None


class DetectionResponse(DetectionBase):
    """Schema for detection response"""
    detection_id: int
    detected_geometry: Optional[GeoJSONGeometry] = None
    analysis_date: datetime
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Violation Schemas
class ViolationBase(BaseModel):
    """Base violation schema"""
    plot_id: str
    violation_type: ViolationType
    severity: Severity
    confidence_score: float = Field(..., ge=0, le=1)
    description: Optional[str] = None
    recommended_action: str


class ViolationCreate(ViolationBase):
    """Schema for creating violation record"""
    detection_id: Optional[int] = None
    evidence_geometry: Optional[GeoJSONGeometry] = None
    evidence_image_url: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: int = Field(3, ge=1, le=5)


class ViolationUpdate(BaseModel):
    """Schema for updating violation"""
    is_resolved: Optional[bool] = None
    resolution_notes: Optional[str] = None
    field_verified: Optional[bool] = None
    verification_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)


class ViolationResponse(ViolationBase):
    """Schema for violation response"""
    violation_id: int
    detection_id: Optional[int] = None
    evidence_geometry: Optional[GeoJSONGeometry] = None
    evidence_image_url: Optional[str] = None
    is_resolved: bool
    resolution_date: Optional[datetime] = None
    field_verified: bool
    verification_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    priority: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Satellite Data Schemas
class SatelliteDataRequest(BaseModel):
    """Schema for satellite data request"""
    plot_id: str
    start_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class SatelliteDataResponse(BaseModel):
    """Schema for satellite data response"""
    rgb_url: Optional[str] = None
    ndvi_url: Optional[str] = None
    ndbi_url: Optional[str] = None
    thermal_url: Optional[str] = None
    metadata: Dict[str, Any]


# Analysis Schemas
class AnalysisRequest(BaseModel):
    """Schema for analysis request"""
    plot_id: str
    start_date: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    include_thermal: bool = True
    include_change_detection: bool = True


class AnalysisResult(BaseModel):
    """Schema for analysis result"""
    plot_id: str
    detection: DetectionResponse
    violations: List[ViolationResponse]
    satellite_data: SatelliteDataResponse
    analysis_summary: Dict[str, Any]


# Dashboard Schemas
class ViolationStatistics(BaseModel):
    """Schema for violation statistics"""
    total_violations: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    unresolved_count: int
    high_priority_count: int


class MonitoringSummary(BaseModel):
    """Schema for monitoring dashboard summary"""
    total_plots: int
    active_plots: int
    total_area_monitored: float
    violations: ViolationStatistics
    recent_detections: List[DetectionResponse]
    last_updated: datetime


# Error Response Schema
class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# CSIDC Portal Schemas
class CSIDCAreaBase(BaseModel):
    """Base schema for CSIDC areas"""
    name: str
    area_type: CSIDCAreaType
    status: AreaStatus = AreaStatus.OPERATIONAL
    size_hectares: Optional[float] = None
    district: Optional[str] = None
    authority: Optional[str] = None
    contact_info: Optional[str] = None


class CSIDCAreaCreate(CSIDCAreaBase):
    """Schema for creating CSIDC area"""
    geometry: GeoJSONGeometry
    established_date: Optional[datetime] = None
    portal_id: Optional[str] = None


class CSIDCAreaUpdate(BaseModel):
    """Schema for updating CSIDC area"""
    name: Optional[str] = None
    status: Optional[AreaStatus] = None
    size_hectares: Optional[float] = None
    authority: Optional[str] = None
    contact_info: Optional[str] = None


class CSIDCAreaResponse(CSIDCAreaBase):
    """Schema for CSIDC area response"""
    area_id: int
    geometry: GeoJSONGeometry
    established_date: Optional[datetime] = None
    portal_id: Optional[str] = None
    last_updated_portal: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class IndustrialAreaBase(BaseModel):
    """Base schema for industrial areas"""
    industry_category: Optional[str] = None
    total_plots: int = 0
    occupied_plots: int = 0
    power_capacity: Optional[str] = None
    water_supply: bool = False
    sewage_treatment: bool = False
    road_connectivity: Optional[str] = None
    total_investment: Optional[float] = None
    employment_generated: Optional[int] = None


class IndustrialAreaCreate(IndustrialAreaBase):
    """Schema for creating industrial area details"""
    csidc_area_id: int
    banking_facilities: bool = False
    training_center: bool = False
    fire_safety: bool = False


class IndustrialAreaResponse(IndustrialAreaBase):
    """Schema for industrial area response"""
    industrial_area_id: int
    csidc_area_id: int
    occupancy_rate: Optional[float] = None
    banking_facilities: bool
    training_center: bool
    fire_safety: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AmenityBase(BaseModel):
    """Base schema for amenities"""
    name: str
    amenity_type: AmenityType
    description: Optional[str] = None
    status: AreaStatus = AreaStatus.OPERATIONAL
    capacity: Optional[str] = None
    operating_hours: Optional[str] = None
    contact_info: Optional[str] = None
    serves_areas: Optional[str] = None
    service_radius_km: Optional[float] = None


class AmenityCreate(AmenityBase):
    """Schema for creating amenity"""
    geometry: GeoJSONGeometry
    area_id: Optional[int] = None
    portal_id: Optional[str] = None


class AmenityResponse(AmenityBase):
    """Schema for amenity response"""
    amenity_id: int
    area_id: Optional[int] = None
    geometry: GeoJSONGeometry
    portal_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DroneDataCollectionBase(BaseModel):
    """Base schema for drone data collection"""
    survey_date: datetime
    survey_type: str
    drone_model: Optional[str] = None
    operator_name: Optional[str] = None
    flight_height_m: Optional[float] = None
    ground_resolution_cm: Optional[float] = None
    weather_conditions: Optional[str] = None


class DroneDataCollectionCreate(DroneDataCollectionBase):
    """Schema for creating drone data collection record"""
    area_id: Optional[int] = None
    plot_id: Optional[str] = None
    survey_geometry: GeoJSONGeometry
    image_count: int = 0
    video_duration_min: Optional[float] = None


class DroneDataCollectionResponse(DroneDataCollectionBase):
    """Schema for drone data collection response"""
    collection_id: int
    area_id: Optional[int] = None
    plot_id: Optional[str] = None
    survey_geometry: GeoJSONGeometry
    image_count: int
    video_duration_min: Optional[float] = None
    data_size_gb: Optional[float] = None
    raw_data_path: Optional[str] = None
    processed_data_path: Optional[str] = None
    violations_detected: int
    change_areas_sqm: Optional[float] = None
    analysis_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Portal Integration Schemas
class PortalSyncResponse(BaseModel):
    """Schema for portal sync response"""
    sync_id: int
    area_type: CSIDCAreaType
    sync_timestamp: datetime
    status: str
    records_fetched: int
    records_updated: int
    records_created: int
    records_failed: int
    error_message: Optional[str] = None
    initiated_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class CSIDCDataRequest(BaseModel):
    """Schema for CSIDC portal data request"""
    area_type: CSIDCAreaType
    bbox: Optional[List[float]] = Field(None, min_items=4, max_items=4)
    force_refresh: bool = False


class CSIDCPortalStats(BaseModel):
    """Schema for CSIDC portal statistics"""
    industrial_areas: Dict[str, int]
    land_banks: Dict[str, int]
    amenities: Dict[str, int]
    total_area_hectares: float
    districts: List[str]
    last_updated: datetime


class ExportRequest(BaseModel):
    """Schema for data export request"""
    area_types: List[CSIDCAreaType]
    format: str = Field(..., regex="^(geojson|shapefile|kml|csv)$")
    bbox: Optional[List[float]] = Field(None, min_items=4, max_items=4)
    include_amenities: bool = True
    include_analysis_data: bool = False
