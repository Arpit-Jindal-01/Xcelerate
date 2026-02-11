"""
Drone Data Collection API Router
Handles drone survey data endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import json
import os

from ..database.connection import get_db
from ..database import models, schemas
from ..services.spatial_service import get_spatial_service, SpatialService
from ..utils.logger import get_logger, log_api_request, log_api_response, log_error
from ..utils.config import settings

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/drone", tags=["Drone Surveys"])


@router.get("/collections", response_model=List[schemas.DroneDataCollectionResponse])
async def get_drone_collections(
    area_id: Optional[int] = Query(None, description="Filter by CSIDC area ID"),
    plot_id: Optional[str] = Query(None, description="Filter by plot ID"),
    survey_type: Optional[str] = Query(None, description="Filter by survey type"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get drone data collections with optional filtering
    """
    try:
        log_api_request("get_drone_collections", {
            "area_id": area_id, "plot_id": plot_id, "survey_type": survey_type
        })
        
        query = db.query(models.DroneDataCollection)
        
        # Apply filters
        if area_id:
            query = query.filter(models.DroneDataCollection.area_id == area_id)
        if plot_id:
            query = query.filter(models.DroneDataCollection.plot_id == plot_id)
        if survey_type:
            query = query.filter(models.DroneDataCollection.survey_type.ilike(f"%{survey_type}%"))
        if date_from:
            query = query.filter(models.DroneDataCollection.survey_date >= date_from)
        if date_to:
            query = query.filter(models.DroneDataCollection.survey_date <= date_to)
        
        # Order by date descending
        query = query.order_by(models.DroneDataCollection.survey_date.desc())
        
        # Apply pagination
        collections = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        response_data = []
        spatial_service = SpatialService(db)
        
        for collection in collections:
            collection_dict = {
                "collection_id": collection.collection_id,
                "area_id": collection.area_id,
                "plot_id": collection.plot_id,
                "survey_date": collection.survey_date,
                "survey_type": collection.survey_type,
                "drone_model": collection.drone_model,
                "operator_name": collection.operator_name,
                "flight_height_m": collection.flight_height_m,
                "ground_resolution_cm": collection.ground_resolution_cm,
                "weather_conditions": collection.weather_conditions,
                "survey_geometry": spatial_service.geometry_to_geojson(collection.survey_geometry),
                "image_count": collection.image_count,
                "video_duration_min": collection.video_duration_min,
                "data_size_gb": collection.data_size_gb,
                "raw_data_path": collection.raw_data_path,
                "processed_data_path": collection.processed_data_path,
                "violations_detected": collection.violations_detected,
                "change_areas_sqm": collection.change_areas_sqm,
                "analysis_completed": collection.analysis_completed,
                "created_at": collection.created_at,
                "updated_at": collection.updated_at
            }
            response_data.append(collection_dict)
        
        log_api_response("get_drone_collections", {"count": len(response_data)})
        return response_data
        
    except Exception as e:
        log_error(e, "get_drone_collections")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving drone collections: {str(e)}"
        )


@router.get("/collections/{collection_id}", response_model=schemas.DroneDataCollectionResponse)
async def get_drone_collection(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific drone data collection by ID
    """
    try:
        log_api_request("get_drone_collection", {"collection_id": collection_id})
        
        collection = db.query(models.DroneDataCollection).filter(
            models.DroneDataCollection.collection_id == collection_id
        ).first()
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drone collection with ID {collection_id} not found"
            )
        
        spatial_service = SpatialService(db)
        collection_dict = {
            "collection_id": collection.collection_id,
            "area_id": collection.area_id,
            "plot_id": collection.plot_id,
            "survey_date": collection.survey_date,
            "survey_type": collection.survey_type,
            "drone_model": collection.drone_model,
            "operator_name": collection.operator_name,
            "flight_height_m": collection.flight_height_m,
            "ground_resolution_cm": collection.ground_resolution_cm,
            "weather_conditions": collection.weather_conditions,
            "survey_geometry": spatial_service.geometry_to_geojson(collection.survey_geometry),
            "image_count": collection.image_count,
            "video_duration_min": collection.video_duration_min,
            "data_size_gb": collection.data_size_gb,
            "raw_data_path": collection.raw_data_path,
            "processed_data_path": collection.processed_data_path,
            "violations_detected": collection.violations_detected,
            "change_areas_sqm": collection.change_areas_sqm,
            "analysis_completed": collection.analysis_completed,
            "created_at": collection.created_at,
            "updated_at": collection.updated_at
        }
        
        log_api_response("get_drone_collection", {"collection_id": collection_id})
        return collection_dict
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "get_drone_collection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving drone collection: {str(e)}"
        )


@router.post("/collections", response_model=schemas.DroneDataCollectionResponse)
async def create_drone_collection(
    collection_data: schemas.DroneDataCollectionCreate,
    db: Session = Depends(get_db)
):
    """
    Create new drone data collection record
    """
    try:
        log_api_request("create_drone_collection", {
            "survey_type": collection_data.survey_type,
            "survey_date": collection_data.survey_date
        })
        
        spatial_service = SpatialService(db)
        
        # Validate area_id or plot_id exists
        if collection_data.area_id:
            area = db.query(models.CSIDCArea).filter(
                models.CSIDCArea.area_id == collection_data.area_id
            ).first()
            if not area:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"CSIDC area with ID {collection_data.area_id} not found"
                )
        
        if collection_data.plot_id:
            plot = db.query(models.Plot).filter(
                models.Plot.plot_id == collection_data.plot_id
            ).first()
            if not plot:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Plot with ID {collection_data.plot_id} not found"
                )
        
        # Create new collection record
        new_collection = models.DroneDataCollection(
            area_id=collection_data.area_id,
            plot_id=collection_data.plot_id,
            survey_date=collection_data.survey_date,
            survey_type=collection_data.survey_type,
            drone_model=collection_data.drone_model,
            operator_name=collection_data.operator_name,
            flight_height_m=collection_data.flight_height_m,
            ground_resolution_cm=collection_data.ground_resolution_cm,
            weather_conditions=collection_data.weather_conditions,
            survey_geometry=spatial_service.geojson_to_geometry(collection_data.survey_geometry),
            image_count=collection_data.image_count,
            video_duration_min=collection_data.video_duration_min
        )
        
        db.add(new_collection)
        db.commit()
        db.refresh(new_collection)
        
        # Prepare response
        collection_dict = {
            "collection_id": new_collection.collection_id,
            "area_id": new_collection.area_id,
            "plot_id": new_collection.plot_id,
            "survey_date": new_collection.survey_date,
            "survey_type": new_collection.survey_type,
            "drone_model": new_collection.drone_model,
            "operator_name": new_collection.operator_name,
            "flight_height_m": new_collection.flight_height_m,
            "ground_resolution_cm": new_collection.ground_resolution_cm,
            "weather_conditions": new_collection.weather_conditions,
            "survey_geometry": spatial_service.geometry_to_geojson(new_collection.survey_geometry),
            "image_count": new_collection.image_count,
            "video_duration_min": new_collection.video_duration_min,
            "data_size_gb": new_collection.data_size_gb,
            "raw_data_path": new_collection.raw_data_path,
            "processed_data_path": new_collection.processed_data_path,
            "violations_detected": new_collection.violations_detected,
            "change_areas_sqm": new_collection.change_areas_sqm,
            "analysis_completed": new_collection.analysis_completed,
            "created_at": new_collection.created_at,
            "updated_at": new_collection.updated_at
        }
        
        log_api_response("create_drone_collection", {"collection_id": new_collection.collection_id})
        return collection_dict
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(e, "create_drone_collection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating drone collection: {str(e)}"
        )


@router.post("/collections/{collection_id}/upload")
async def upload_drone_data(
    collection_id: int,
    file: UploadFile = File(...),
    data_type: str = Query(..., regex="^(raw|processed|ortho)$", description="Type of data being uploaded"),
    db: Session = Depends(get_db)
):
    """
    Upload drone survey data files
    """
    try:
        log_api_request("upload_drone_data", {
            "collection_id": collection_id,
            "filename": file.filename,
            "data_type": data_type
        })
        
        # Get collection record
        collection = db.query(models.DroneDataCollection).filter(
            models.DroneDataCollection.collection_id == collection_id
        ).first()
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drone collection with ID {collection_id} not found"
            )
        
        # Create upload directory if not exists
        upload_dir = os.path.join(settings.DATA_STORAGE_PATH, "drone_data", str(collection_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, f"{data_type}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update collection record with file path
        if data_type == "raw":
            collection.raw_data_path = file_path
        elif data_type == "processed":
            collection.processed_data_path = file_path
        elif data_type == "ortho":
            collection.ortho_mosaic_path = file_path
        
        # Update file size
        file_size_gb = len(content) / (1024**3)  # Convert to GB
        if collection.data_size_gb:
            collection.data_size_gb += file_size_gb
        else:
            collection.data_size_gb = file_size_gb
        
        db.commit()
        
        log_api_response("upload_drone_data", {
            "collection_id": collection_id,
            "file_path": file_path,
            "size_gb": file_size_gb
        })
        
        return JSONResponse(
            content={
                "message": "File uploaded successfully",
                "collection_id": collection_id,
                "file_path": file_path,
                "data_type": data_type,
                "size_gb": file_size_gb
            },
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "upload_drone_data")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading drone data: {str(e)}"
        )


@router.post("/collections/{collection_id}/analyze")
async def analyze_drone_data(
    collection_id: int,
    include_change_detection: bool = Query(True, description="Include change detection analysis"),
    include_violation_detection: bool = Query(True, description="Include violation detection"),
    db: Session = Depends(get_db)
):
    """
    Trigger analysis of drone survey data
    """
    try:
        log_api_request("analyze_drone_data", {
            "collection_id": collection_id,
            "change_detection": include_change_detection,
            "violation_detection": include_violation_detection
        })
        
        # Get collection record
        collection = db.query(models.DroneDataCollection).filter(
            models.DroneDataCollection.collection_id == collection_id
        ).first()
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drone collection with ID {collection_id} not found"
            )
        
        # Check if data files exist
        if not collection.raw_data_path or not os.path.exists(collection.raw_data_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Raw drone data not found. Please upload data files first."
            )
        
        # TODO: Implement actual analysis pipeline
        # For now, simulate analysis results
        
        # Update collection with mock analysis results
        collection.violations_detected = 2  # Mock result
        collection.change_areas_sqm = 1250.5  # Mock result
        collection.analysis_completed = True
        
        # Calculate image quality score (mock)
        collection.image_quality_score = 0.85
        collection.coverage_completeness = 0.95
        
        db.commit()
        
        log_api_response("analyze_drone_data", {
            "collection_id": collection_id,
            "violations_detected": collection.violations_detected,
            "change_areas_sqm": collection.change_areas_sqm
        })
        
        return JSONResponse(
            content={
                "message": "Analysis completed successfully",
                "collection_id": collection_id,
                "violations_detected": collection.violations_detected,
                "change_areas_sqm": collection.change_areas_sqm,
                "analysis_completed": True,
                "quality_metrics": {
                    "image_quality_score": collection.image_quality_score,
                    "coverage_completeness": collection.coverage_completeness
                }
            },
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "analyze_drone_data")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing drone data: {str(e)}"
        )


@router.get("/statistics")
async def get_drone_statistics(
    date_from: Optional[date] = Query(None, description="Statistics from date"),
    date_to: Optional[date] = Query(None, description="Statistics to date"),
    db: Session = Depends(get_db)
):
    """
    Get drone survey statistics
    """
    try:
        log_api_request("get_drone_statistics", {"date_from": date_from, "date_to": date_to})
        
        query = db.query(models.DroneDataCollection)
        
        # Apply date filter
        if date_from:
            query = query.filter(models.DroneDataCollection.survey_date >= date_from)
        if date_to:
            query = query.filter(models.DroneDataCollection.survey_date <= date_to)
        
        # Calculate statistics
        total_surveys = query.count()
        completed_analysis = query.filter(models.DroneDataCollection.analysis_completed == True).count()
        total_violations = query.with_entities(
            func.sum(models.DroneDataCollection.violations_detected)
        ).scalar() or 0
        total_data_gb = query.with_entities(
            func.sum(models.DroneDataCollection.data_size_gb)
        ).scalar() or 0
        
        # Survey type breakdown
        survey_types = {}
        for survey_type in ["routine", "violation_check", "baseline", "special"]:
            count = query.filter(
                models.DroneDataCollection.survey_type.ilike(f"%{survey_type}%")
            ).count()
            survey_types[survey_type] = count
        
        # Average metrics
        avg_quality = query.with_entities(
            func.avg(models.DroneDataCollection.image_quality_score)
        ).scalar() or 0
        avg_coverage = query.with_entities(
            func.avg(models.DroneDataCollection.coverage_completeness)
        ).scalar() or 0
        
        statistics = {
            "total_surveys": total_surveys,
            "completed_analysis": completed_analysis,
            "analysis_completion_rate": (completed_analysis / total_surveys * 100) if total_surveys > 0 else 0,
            "total_violations_detected": int(total_violations),
            "total_data_storage_gb": round(float(total_data_gb), 2),
            "survey_types": survey_types,
            "average_image_quality": round(float(avg_quality), 3),
            "average_coverage_completeness": round(float(avg_coverage), 3),
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None
            },
            "generated_at": datetime.now()
        }
        
        log_api_response("get_drone_statistics", {"total_surveys": total_surveys})
        return statistics
        
    except Exception as e:
        log_error(e, "get_drone_statistics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving drone statistics: {str(e)}"
        )