"""
Database Models for Industrial Land Monitoring System
Uses SQLAlchemy with GeoAlchemy2 for PostGIS support
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey,
    Boolean, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from datetime import datetime
import enum

from .connection import Base
from ..utils.config import settings


# Enumerations
class ViolationType(enum.Enum):
    """Types of land use violations"""
    ENCROACHMENT = "encroachment"
    ILLEGAL_CONSTRUCTION = "illegal_construction"
    UNUSED_LAND = "unused_land"
    SUSPICIOUS_CHANGE = "suspicious_change"
    COMPLIANT = "compliant"


class Severity(enum.Enum):
    """Severity levels for violations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LandUseType(enum.Enum):
    """Approved land use types"""
    INDUSTRIAL = "industrial"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"
    WAREHOUSE = "warehouse"
    MANUFACTURING = "manufacturing"
    LOGISTICS = "logistics"


class CSIDCAreaType(enum.Enum):
    """CSIDC area types from portal"""
    INDUSTRIAL_AREA = "industrial_area"
    LAND_BANK = "land_bank"
    OLD_INDUSTRIAL = "old_industrial"
    DIRECTORATE_INDUSTRIAL = "directorate_industrial"
    AMENITY = "amenity"


class AreaStatus(enum.Enum):
    """Status of CSIDC areas"""
    OPERATIONAL = "operational"
    AVAILABLE = "available"
    UNDER_DEVELOPMENT = "under_development"
    PLANNED = "planned"
    CLOSED = "closed"


class AmenityType(enum.Enum):
    """Types of amenities"""
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    INFRASTRUCTURE = "infrastructure"
    TRANSPORTATION = "transportation"
    UTILITIES = "utilities"
    FINANCE = "finance"
    RECREATION = "recreation"


# Database Models
class Plot(Base):
    """
    Represents an industrial plot/parcel
    """
    __tablename__ = "plots"
    
    plot_id = Column(String(50), primary_key=True, index=True)
    
    # Spatial data (PostGIS Geometry)
    geometry = Column(
        Geometry(geometry_type='POLYGON', srid=settings.SRID),
        nullable=False
    )
    
    # Plot information
    approved_area = Column(Float, nullable=False, comment="Approved area in square meters")
    approved_land_use = Column(SQLEnum(LandUseType), nullable=False)
    industry_type = Column(String(100), nullable=True)
    industry_name = Column(String(200), nullable=True)
    
    # Owner information
    owner_name = Column(String(200), nullable=True)
    owner_contact = Column(String(100), nullable=True)
    
    # Administrative
    allotment_date = Column(DateTime, nullable=True)
    lease_expiry = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    detections = relationship("Detection", back_populates="plot", cascade="all, delete-orphan")
    violations = relationship("Violation", back_populates="plot", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Plot {self.plot_id} - {self.industry_name}>"


class Detection(Base):
    """
    Represents automated detection results from satellite/ML analysis
    """
    __tablename__ = "detections"
    
    detection_id = Column(Integer, primary_key=True, autoincrement=True)
    plot_id = Column(String(50), ForeignKey("plots.plot_id"), nullable=False, index=True)
    
    # Detection metrics
    built_up_area = Column(Float, nullable=True, comment="Detected built-up area in sq m")
    heat_signature_area = Column(Float, nullable=True, comment="Area with thermal signature")
    change_score = Column(Float, nullable=True, comment="Change detection confidence (0-1)")
    vegetation_index = Column(Float, nullable=True, comment="Average NDVI")
    built_up_index = Column(Float, nullable=True, comment="Average NDBI")
    
    # Detected geometry (may differ from plot boundary)
    detected_geometry = Column(
        Geometry(geometry_type='POLYGON', srid=settings.SRID),
        nullable=True
    )
    
    # Source data information
    sentinel_date = Column(DateTime, nullable=True)
    landsat_date = Column(DateTime, nullable=True)
    analysis_date = Column(DateTime, server_default=func.now())
    
    # ML model versions
    model_version_unet = Column(String(50), nullable=True)
    model_version_siamese = Column(String(50), nullable=True)
    
    # Metadata
    timestamp = Column(DateTime, server_default=func.now())
    
    # Relationships
    plot = relationship("Plot", back_populates="detections")
    
    def __repr__(self):
        return f"<Detection {self.detection_id} for Plot {self.plot_id}>"


class Violation(Base):
    """
    Represents detected violations with recommendations
    """
    __tablename__ = "violations"
    
    violation_id = Column(Integer, primary_key=True, autoincrement=True)
    plot_id = Column(String(50), ForeignKey("plots.plot_id"), nullable=False, index=True)
    detection_id = Column(Integer, ForeignKey("detections.detection_id"), nullable=True)
    
    # Violation details
    violation_type = Column(SQLEnum(ViolationType), nullable=False, index=True)
    severity = Column(SQLEnum(Severity), nullable=False)
    confidence_score = Column(Float, nullable=False, comment="Confidence 0-1")
    
    # Description and recommendation
    description = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=False)
    
    # Evidence
    evidence_geometry = Column(
        Geometry(geometry_type='POLYGON', srid=settings.SRID),
        nullable=True
    )
    evidence_image_url = Column(String(500), nullable=True)
    
    # Status tracking
    is_resolved = Column(Boolean, default=False)
    resolution_date = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Field verification
    field_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Administrative
    assigned_to = Column(String(100), nullable=True, comment="Inspector/Officer name")
    priority = Column(Integer, default=3, comment="1=Urgent, 5=Low")
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    plot = relationship("Plot", back_populates="violations")
    
    def __repr__(self):
        return f"<Violation {self.violation_id} - {self.violation_type.value} ({self.severity.value})>"


class AnalysisJob(Base):
    """
    Tracks batch analysis jobs for monitoring
    """
    __tablename__ = "analysis_jobs"
    
    job_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Job details
    job_type = Column(String(50), nullable=False)  # 'full_scan', 'targeted', 'scheduled'
    status = Column(String(20), nullable=False)  # 'pending', 'running', 'completed', 'failed'
    
    # Scope
    plot_ids = Column(Text, nullable=True, comment="Comma-separated plot IDs")
    date_range_start = Column(DateTime, nullable=True)
    date_range_end = Column(DateTime, nullable=True)
    
    # Progress
    total_plots = Column(Integer, default=0)
    processed_plots = Column(Integer, default=0)
    violations_found = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<AnalysisJob {self.job_id} - {self.status}>"


class CSIDCArea(Base):
    """
    Base model for CSIDC areas from portal integration
    Represents industrial areas, land banks, and amenities
    """
    __tablename__ = "csidc_areas"
    
    area_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic information
    name = Column(String(200), nullable=False)
    area_type = Column(SQLEnum(CSIDCAreaType), nullable=False, index=True)
    status = Column(SQLEnum(AreaStatus), nullable=False, default=AreaStatus.OPERATIONAL)
    
    # Spatial data
    geometry = Column(
        Geometry(geometry_type='POLYGON', srid=settings.SRID),
        nullable=False
    )
    
    # Area details
    size_hectares = Column(Float, nullable=True)
    district = Column(String(100), nullable=True)
    established_date = Column(DateTime, nullable=True)
    
    # Administrative details
    authority = Column(String(200), nullable=True)
    contact_info = Column(Text, nullable=True)
    
    # Portal integration
    portal_id = Column(String(100), nullable=True, unique=True)
    last_updated_portal = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    amenities = relationship("Amenity", back_populates="area", cascade="all, delete-orphan")
    industrial_areas = relationship("IndustrialArea", back_populates="csidc_area")
    
    def __repr__(self):
        return f"<CSIDCArea {self.area_id} - {self.name} ({self.area_type.value})>"


class IndustrialArea(Base):
    """
    Detailed industrial area information extending CSIDCArea
    """
    __tablename__ = "industrial_areas"
    
    industrial_area_id = Column(Integer, primary_key=True, autoincrement=True)
    csidc_area_id = Column(Integer, ForeignKey("csidc_areas.area_id"), nullable=False)
    
    # Industrial-specific details
    industry_category = Column(String(100), nullable=True)
    total_plots = Column(Integer, default=0)
    occupied_plots = Column(Integer, default=0)
    occupancy_rate = Column(Float, nullable=True, comment="Percentage occupied")
    
    # Infrastructure
    power_capacity = Column(String(50), nullable=True)
    water_supply = Column(Boolean, default=False)
    sewage_treatment = Column(Boolean, default=False)
    road_connectivity = Column(String(100), nullable=True)
    
    # Investment details
    total_investment = Column(Float, nullable=True, comment="Total investment in crores")
    employment_generated = Column(Integer, nullable=True)
    
    # Services available
    banking_facilities = Column(Boolean, default=False)
    training_center = Column(Boolean, default=False)
    fire_safety = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    csidc_area = relationship("CSIDCArea", back_populates="industrial_areas")
    
    def __repr__(self):
        return f"<IndustrialArea {self.industrial_area_id} - {self.csidc_area.name if self.csidc_area else 'Unknown'}>"


class Amenity(Base):
    """
    Amenities within or serving CSIDC areas
    """
    __tablename__ = "amenities"
    
    amenity_id = Column(Integer, primary_key=True, autoincrement=True)
    area_id = Column(Integer, ForeignKey("csidc_areas.area_id"), nullable=True)
    
    # Amenity details
    name = Column(String(200), nullable=False)
    amenity_type = Column(SQLEnum(AmenityType), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Location (can be point or polygon)
    geometry = Column(
        Geometry(geometry_type='GEOMETRY', srid=settings.SRID),
        nullable=False
    )
    
    # Operational details
    status = Column(SQLEnum(AreaStatus), nullable=False, default=AreaStatus.OPERATIONAL)
    capacity = Column(String(100), nullable=True)
    operating_hours = Column(String(100), nullable=True)
    contact_info = Column(Text, nullable=True)
    
    # Service area
    serves_areas = Column(Text, nullable=True, comment="Comma-separated area names served")
    service_radius_km = Column(Float, nullable=True)
    
    # Portal integration
    portal_id = Column(String(100), nullable=True, unique=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    area = relationship("CSIDCArea", back_populates="amenities")
    
    def __repr__(self):
        return f"<Amenity {self.amenity_id} - {self.name} ({self.amenity_type.value})>"


class DroneDataCollection(Base):
    """
    Drone survey data collection records for areas
    Links with hackathon drone survey requirements
    """
    __tablename__ = "drone_collections"
    
    collection_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Area reference
    area_id = Column(Integer, ForeignKey("csidc_areas.area_id"), nullable=True)
    plot_id = Column(String(50), ForeignKey("plots.plot_id"), nullable=True)
    
    # Survey details
    survey_date = Column(DateTime, nullable=False)
    survey_type = Column(String(50), nullable=False)  # 'routine', 'violation_check', 'baseline'
    drone_model = Column(String(100), nullable=True)
    operator_name = Column(String(100), nullable=True)
    
    # Flight parameters
    flight_height_m = Column(Float, nullable=True)
    ground_resolution_cm = Column(Float, nullable=True)
    weather_conditions = Column(String(200), nullable=True)
    
    # Coverage area
    survey_geometry = Column(
        Geometry(geometry_type='POLYGON', srid=settings.SRID),
        nullable=False
    )
    
    # Data outputs
    image_count = Column(Integer, default=0)
    video_duration_min = Column(Float, nullable=True)
    data_size_gb = Column(Float, nullable=True)
    
    # Storage paths
    raw_data_path = Column(String(500), nullable=True)
    processed_data_path = Column(String(500), nullable=True)
    ortho_mosaic_path = Column(String(500), nullable=True)
    
    # Analysis results
    violations_detected = Column(Integer, default=0)
    change_areas_sqm = Column(Float, nullable=True)
    analysis_completed = Column(Boolean, default=False)
    
    # Quality metrics
    image_quality_score = Column(Float, nullable=True, comment="0-1 quality score")
    coverage_completeness = Column(Float, nullable=True, comment="Percentage covered")
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<DroneCollection {self.collection_id} - {self.survey_date.strftime('%Y-%m-%d') if self.survey_date else 'Unknown'}>"


class PortalSync(Base):
    """
    Track synchronization with CSIDC portal
    """
    __tablename__ = "portal_syncs"
    
    sync_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Sync details
    area_type = Column(SQLEnum(CSIDCAreaType), nullable=False)
    sync_timestamp = Column(DateTime, server_default=func.now())
    status = Column(String(20), nullable=False)  # 'success', 'partial', 'failed'
    
    # Results
    records_fetched = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Metadata
    initiated_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<PortalSync {self.sync_id} - {self.area_type.value} ({self.status})>"


# Indexes for performance
from sqlalchemy import Index

# Spatial indexes are automatically created by PostGIS
# Existing indexes for common queries
Index('idx_plot_active', Plot.is_active)
Index('idx_plot_land_use', Plot.approved_land_use)
Index('idx_detection_analysis_date', Detection.analysis_date)
Index('idx_violation_type_severity', Violation.violation_type, Violation.severity)
Index('idx_violation_resolved', Violation.is_resolved)
Index('idx_violation_created', Violation.created_at)

# New indexes for CSIDC models
Index('idx_csidc_area_type', CSIDCArea.area_type)
Index('idx_csidc_area_status', CSIDCArea.status)
Index('idx_csidc_area_district', CSIDCArea.district)
Index('idx_csidc_area_portal_id', CSIDCArea.portal_id)
Index('idx_amenity_type', Amenity.amenity_type)
Index('idx_amenity_status', Amenity.status)
Index('idx_drone_survey_date', DroneDataCollection.survey_date)
Index('idx_drone_survey_type', DroneDataCollection.survey_type)
Index('idx_portal_sync_type_timestamp', PortalSync.area_type, PortalSync.sync_timestamp)
Index('idx_portal_sync_status', PortalSync.status)
