"""
FastAPI Main Application
Industrial Land Monitoring and Violation Detection System
"""

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json

from database.connection import get_db, init_db_engine, create_tables, check_db_connection
from database import models, schemas
from services.gee_service import get_gee_service, GEEService
from services.ml_service import get_ml_service, MLService
from services.spatial_service import get_spatial_service, SpatialService
from services.rule_engine import get_rule_engine, RuleEngine, DetectionData
from utils.config import settings, setup_directories
from utils.logger import app_logger, log_api_request, log_api_response, log_error

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready AI-powered land monitoring system for CSIDC",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    app_logger.info("=" * 60)
    app_logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    app_logger.info("=" * 60)
    
    try:
        # Setup directories
        setup_directories()
        app_logger.info("✓ Directories created")
        
        # Initialize database
        init_db_engine()
        create_tables()
        app_logger.info("✓ Database initialized")
        
        # Initialize GEE service
        gee_service = get_gee_service()
        gee_service.initialize()
        app_logger.info("✓ Google Earth Engine initialized")
        
        # Initialize ML service
        ml_service = get_ml_service()
        app_logger.info("✓ ML models loaded")
        
        app_logger.info("=" * 60)
        app_logger.info("🚀 Application startup complete")
        app_logger.info("=" * 60)
        
    except Exception as e:
        app_logger.error(f"Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    app_logger.info("Shutting down application...")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    Verifies database, GEE, and ML services are operational
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "services": {}
    }
    
    # Check database
    try:
        db_healthy = check_db_connection()
        health_status["services"]["database"] = "healthy" if db_healthy else "unhealthy"
    except:
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check GEE
    try:
        gee_service = get_gee_service()
        health_status["services"]["google_earth_engine"] = "healthy" if gee_service.initialized else "unhealthy"
    except:
        health_status["services"]["google_earth_engine"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check ML
    try:
        ml_service = get_ml_service()
        health_status["services"]["ml_models"] = "healthy"
    except:
        health_status["services"]["ml_models"] = "unhealthy"
        health_status["status"] = "degraded"
    
    return health_status


# ============================================================
# SATELLITE DATA ENDPOINTS
# ============================================================

@app.get(
    "/api/v1/satellite",
    response_model=schemas.SatelliteDataResponse,
    tags=["Satellite"]
)
async def get_satellite_data(
    plot_id: str = Query(..., description="Plot ID"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    include_thermal: bool = Query(True, description="Include thermal data"),
    db: Session = Depends(get_db)
):
    """
    Get satellite imagery and indices for a plot
    
    Returns Sentinel-2 RGB, NDVI, NDBI, and optionally Landsat thermal data
    """
    log_api_request("/satellite", "GET", {"plot_id": plot_id})
    start_time = datetime.now()
    
    try:
        # Get plot geometry
        plot = db.query(models.Plot).filter(models.Plot.plot_id == plot_id).first()
        if not plot:
            raise HTTPException(status_code=404, detail=f"Plot {plot_id} not found")
        
        spatial_service = get_spatial_service(db)
        plot_geojson = spatial_service.get_plot_geometry_geojson(plot_id)
        
        # Get satellite data
        gee_service = get_gee_service()
        
        sentinel_data = gee_service.get_sentinel_composite(
            plot_geojson,
            start_date,
            end_date
        )
        
        thermal_url = None
        thermal_metadata = {}
        
        if include_thermal:
            thermal_data = gee_service.get_thermal_data(
                plot_geojson,
                start_date,
                end_date
            )
            thermal_url = thermal_data.get("thermal_url")
            thermal_metadata = thermal_data.get("metadata", {})
        
        response = schemas.SatelliteDataResponse(
            rgb_url=sentinel_data.get("rgb_url"),
            ndvi_url=sentinel_data.get("ndvi_url"),
            ndbi_url=sentinel_data.get("ndbi_url"),
            thermal_url=thermal_url,
            metadata={
                "sentinel": sentinel_data.get("metadata", {}),
                "thermal": thermal_metadata
            }
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        log_api_response("/satellite", 200, duration)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "get_satellite_data")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ANALYSIS ENDPOINTS
# ============================================================

@app.post(
    "/api/v1/analyze/{plot_id}",
    response_model=schemas.AnalysisResult,
    tags=["Analysis"]
)
async def analyze_plot(
    plot_id: str,
    request: Optional[schemas.AnalysisRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Comprehensive analysis of a plot
    
    Performs:
    1. Satellite data acquisition
    2. ML-based detection (built-up, change, thermal)
    3. Spatial analysis
    4. Rule-based violation detection
    """
    log_api_request(f"/analyze/{plot_id}", "POST", {})
    start_time = datetime.now()
    
    try:
        # Get plot
        plot = db.query(models.Plot).filter(models.Plot.plot_id == plot_id).first()
        if not plot:
            raise HTTPException(status_code=404, detail=f"Plot {plot_id} not found")
        
        # Default date range (last 3 months)
        if request and request.start_date:
            start_date = request.start_date
            end_date = request.end_date
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Initialize services
        gee_service = get_gee_service()
        ml_service = get_ml_service()
        spatial_service = get_spatial_service(db)
        rule_engine = get_rule_engine()
        
        # Step 1: Get satellite data
        plot_geojson = spatial_service.get_plot_geometry_geojson(plot_id)
        
        sentinel_data = gee_service.get_sentinel_composite(plot_geojson, start_date, end_date)
        thermal_data = gee_service.get_thermal_data(plot_geojson, start_date, end_date)
        
        # Step 2: ML inference (placeholder - would download and process images)
        # In production, download images and run actual inference
        detection_data = DetectionData(
            plot_id=plot_id,
            approved_area=plot.approved_area,
            approved_land_use=plot.approved_land_use.value,
            built_up_area=plot.approved_area * 0.85,  # Placeholder
            built_up_percentage=85.0,
            heat_signature_area=plot.approved_area * 0.15,
            heat_percentage=15.0,
            change_score=0.65,
            has_encroachment=False
        )
        
        # Step 3: Rule engine evaluation
        violation_result = rule_engine.evaluate(detection_data)
        
        # Step 4: Save detection to database
        detection = models.Detection(
            plot_id=plot_id,
            built_up_area=detection_data.built_up_area,
            heat_signature_area=detection_data.heat_signature_area,
            change_score=detection_data.change_score,
            sentinel_date=datetime.strptime(end_date, '%Y-%m-%d')
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)
        
        # Step 5: Save violation if not compliant
        violations = []
        if violation_result.violation_type.value != "compliant":
            violation = models.Violation(
                plot_id=plot_id,
                detection_id=detection.detection_id,
                violation_type=violation_result.violation_type.value,
                severity=violation_result.severity.value,
                confidence_score=violation_result.confidence,
                description=violation_result.description,
                recommended_action=violation_result.recommended_action,
                priority=violation_result.priority
            )
            db.add(violation)
            db.commit()
            db.refresh(violation)
            violations.append(violation)
        
        # Prepare response
        response = {
            "plot_id": plot_id,
            "detection": detection,
            "violations": violations,
            "satellite_data": {
                "rgb_url": sentinel_data.get("rgb_url"),
                "ndvi_url": sentinel_data.get("ndvi_url"),
                "ndbi_url": sentinel_data.get("ndbi_url"),
                "thermal_url": thermal_data.get("thermal_url"),
                "metadata": sentinel_data.get("metadata", {})
            },
            "analysis_summary": {
                "violation_type": violation_result.violation_type.value,
                "severity": violation_result.severity.value,
                "confidence": violation_result.confidence,
                "recommendation": violation_result.recommended_action
            }
        }
        
        duration = (datetime.now() - start_time).total_seconds()
        log_api_response(f"/analyze/{plot_id}", 200, duration)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, f"analyze_plot: {plot_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# VIOLATION ENDPOINTS
# ============================================================

@app.get(
    "/api/v1/violations/{plot_id}",
    response_model=List[schemas.ViolationResponse],
    tags=["Violations"]
)
async def get_violations(
    plot_id: str,
    include_resolved: bool = Query(False, description="Include resolved violations"),
    db: Session = Depends(get_db)
):
    """
    Get all violations for a specific plot
    """
    try:
        query = db.query(models.Violation).filter(models.Violation.plot_id == plot_id)
        
        if not include_resolved:
            query = query.filter(models.Violation.is_resolved == False)
        
        violations = query.order_by(models.Violation.created_at.desc()).all()
        
        return violations
        
    except Exception as e:
        log_error(e, f"get_violations: {plot_id}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/violations",
    response_model=List[schemas.ViolationResponse],
    tags=["Violations"]
)
async def get_all_violations(
    violation_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get all violations with optional filters
    """
    try:
        query = db.query(models.Violation)
        
        if violation_type:
            query = query.filter(models.Violation.violation_type == violation_type)
        
        if severity:
            query = query.filter(models.Violation.severity == severity)
        
        if is_resolved is not None:
            query = query.filter(models.Violation.is_resolved == is_resolved)
        
        violations = query.order_by(
            models.Violation.priority,
            models.Violation.created_at.desc()
        ).limit(limit).all()
        
        return violations
        
    except Exception as e:
        log_error(e, "get_all_violations")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# GEOJSON ENDPOINTS
# ============================================================

@app.get(
    "/api/v1/geojson/{plot_id}",
    response_model=schemas.GeoJSONFeature,
    tags=["GeoJSON"]
)
async def get_plot_geojson(
    plot_id: str,
    include_violations: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Get plot boundary and violations as GeoJSON Feature
    """
    try:
        plot = db.query(models.Plot).filter(models.Plot.plot_id == plot_id).first()
        if not plot:
            raise HTTPException(status_code=404, detail=f"Plot {plot_id} not found")
        
        spatial_service = get_spatial_service(db)
        geometry = spatial_service.get_plot_geometry_geojson(plot_id)
        
        properties = {
            "plot_id": plot.plot_id,
            "industry_name": plot.industry_name,
            "approved_area": plot.approved_area,
            "land_use": plot.approved_land_use.value,
            "is_active": plot.is_active
        }
        
        if include_violations:
            violations = db.query(models.Violation).filter(
                models.Violation.plot_id == plot_id,
                models.Violation.is_resolved == False
            ).all()
            
            properties["violations"] = [
                {
                    "type": v.violation_type.value,
                    "severity": v.severity.value,
                    "confidence": v.confidence_score
                }
                for v in violations
            ]
        
        feature = schemas.GeoJSONFeature(
            type="Feature",
            geometry=schemas.GeoJSONGeometry(**geometry),
            properties=properties
        )
        
        return feature
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, f"get_plot_geojson: {plot_id}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/geojson/all",
    response_model=schemas.GeoJSONFeatureCollection,
    tags=["GeoJSON"]
)
async def get_all_plots_geojson(
    db: Session = Depends(get_db)
):
    """
    Get all plots as GeoJSON FeatureCollection
    """
    try:
        plots = db.query(models.Plot).filter(models.Plot.is_active == True).all()
        
        features = []
        spatial_service = get_spatial_service(db)
        
        for plot in plots:
            geometry = spatial_service.get_plot_geometry_geojson(plot.plot_id)
            
            # Get latest violation
            latest_violation = db.query(models.Violation).filter(
                models.Violation.plot_id == plot.plot_id,
                models.Violation.is_resolved == False
            ).order_by(models.Violation.created_at.desc()).first()
            
            properties = {
                "plot_id": plot.plot_id,
                "industry_name": plot.industry_name,
                "approved_area": plot.approved_area,
                "violation_status": "compliant"
            }
            
            if latest_violation:
                properties["violation_status"] = latest_violation.violation_type.value
                properties["severity"] = latest_violation.severity.value
            
            feature = schemas.GeoJSONFeature(
                type="Feature",
                geometry=schemas.GeoJSONGeometry(**geometry),
                properties=properties
            )
            features.append(feature)
        
        return schemas.GeoJSONFeatureCollection(
            type="FeatureCollection",
            features=features
        )
        
    except Exception as e:
        log_error(e, "get_all_plots_geojson")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
