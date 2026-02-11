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


# Indexes for performance
from sqlalchemy import Index

# Spatial indexes are automatically created by PostGIS
# Additional indexes for common queries
Index('idx_plot_active', Plot.is_active)
Index('idx_plot_land_use', Plot.approved_land_use)
Index('idx_detection_analysis_date', Detection.analysis_date)
Index('idx_violation_type_severity', Violation.violation_type, Violation.severity)
Index('idx_violation_resolved', Violation.is_resolved)
Index('idx_violation_created', Violation.created_at)
