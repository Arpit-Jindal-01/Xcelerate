"""
CSIDC API Router
Handles CSIDC portal integration and area management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from ..database.connection import get_db
from ..database import models, schemas
from ..services.csidc_service import get_csidc_service, CSIDCPortalService
from ..services.spatial_service import get_spatial_service, SpatialService
from ..utils.logger import get_logger, log_api_request, log_api_response, log_error

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/csidc", tags=["CSIDC Portal"])


@router.get("/areas", response_model=List[schemas.CSIDCAreaResponse])
async def get_csidc_areas(
    area_type: Optional[schemas.CSIDCAreaType] = Query(None, description="Filter by area type"),
    district: Optional[str] = Query(None, description="Filter by district"),
    status: Optional[schemas.AreaStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get CSIDC areas with optional filtering
    """
    try:
        log_api_request("get_csidc_areas", {"area_type": area_type, "district": district, "status": status})
        
        query = db.query(models.CSIDCArea)
        
        # Apply filters
        if area_type:
            query = query.filter(models.CSIDCArea.area_type == area_type)
        if district:
            query = query.filter(models.CSIDCArea.district.ilike(f"%{district}%"))
        if status:
            query = query.filter(models.CSIDCArea.status == status)
        
        # Apply pagination
        areas = query.offset(offset).limit(limit).all()
        
        # Convert to response format with geometry
        response_data = []
        spatial_service = SpatialService(db)
        
        for area in areas:
            area_dict = {
                "area_id": area.area_id,
                "name": area.name,
                "area_type": area.area_type,
                "status": area.status,
                "size_hectares": area.size_hectares,
                "district": area.district,
                "authority": area.authority,
                "contact_info": area.contact_info,
                "established_date": area.established_date,
                "portal_id": area.portal_id,
                "last_updated_portal": area.last_updated_portal,
                "created_at": area.created_at,
                "updated_at": area.updated_at,
                "geometry": spatial_service.geometry_to_geojson(area.geometry)
            }
            response_data.append(area_dict)
        
        log_api_response("get_csidc_areas", {"count": len(response_data)})
        return response_data
        
    except Exception as e:
        log_error(e, "get_csidc_areas")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving CSIDC areas: {str(e)}"
        )


@router.get("/areas/{area_id}", response_model=schemas.CSIDCAreaResponse)
async def get_csidc_area(
    area_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific CSIDC area by ID
    """
    try:
        log_api_request("get_csidc_area", {"area_id": area_id})
        
        area = db.query(models.CSIDCArea).filter(models.CSIDCArea.area_id == area_id).first()
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CSIDC area with ID {area_id} not found"
            )
        
        spatial_service = SpatialService(db)
        area_dict = {
            "area_id": area.area_id,
            "name": area.name,
            "area_type": area.area_type,
            "status": area.status,
            "size_hectares": area.size_hectares,
            "district": area.district,
            "authority": area.authority,
            "contact_info": area.contact_info,
            "established_date": area.established_date,
            "portal_id": area.portal_id,
            "last_updated_portal": area.last_updated_portal,
            "created_at": area.created_at,
            "updated_at": area.updated_at,
            "geometry": spatial_service.geometry_to_geojson(area.geometry)
        }
        
        log_api_response("get_csidc_area", {"area_id": area_id})
        return area_dict
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "get_csidc_area")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving CSIDC area: {str(e)}"
        )


@router.post("/areas", response_model=schemas.CSIDCAreaResponse)
async def create_csidc_area(
    area_data: schemas.CSIDCAreaCreate,
    db: Session = Depends(get_db)
):
    """
    Create new CSIDC area
    """
    try:
        log_api_request("create_csidc_area", {"name": area_data.name, "type": area_data.area_type})
        
        spatial_service = SpatialService(db)
        
        # Create new area
        new_area = models.CSIDCArea(
            name=area_data.name,
            area_type=area_data.area_type,
            status=area_data.status,
            size_hectares=area_data.size_hectares,
            district=area_data.district,
            authority=area_data.authority,
            contact_info=area_data.contact_info,
            established_date=area_data.established_date,
            portal_id=area_data.portal_id,
            geometry=spatial_service.geojson_to_geometry(area_data.geometry)
        )
        
        db.add(new_area)
        db.commit()
        db.refresh(new_area)
        
        # Prepare response
        area_dict = {
            "area_id": new_area.area_id,
            "name": new_area.name,
            "area_type": new_area.area_type,
            "status": new_area.status,
            "size_hectares": new_area.size_hectares,
            "district": new_area.district,
            "authority": new_area.authority,
            "contact_info": new_area.contact_info,
            "established_date": new_area.established_date,
            "portal_id": new_area.portal_id,
            "last_updated_portal": new_area.last_updated_portal,
            "created_at": new_area.created_at,
            "updated_at": new_area.updated_at,
            "geometry": spatial_service.geometry_to_geojson(new_area.geometry)
        }
        
        log_api_response("create_csidc_area", {"area_id": new_area.area_id})
        return area_dict
        
    except Exception as e:
        db.rollback()
        log_error(e, "create_csidc_area")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating CSIDC area: {str(e)}"
        )


@router.get("/amenities", response_model=List[schemas.AmenityResponse])
async def get_amenities(
    amenity_type: Optional[schemas.AmenityType] = Query(None, description="Filter by amenity type"),
    area_id: Optional[int] = Query(None, description="Filter by CSIDC area ID"),
    status: Optional[schemas.AreaStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get amenities with optional filtering
    """
    try:
        log_api_request("get_amenities", {"amenity_type": amenity_type, "area_id": area_id})
        
        query = db.query(models.Amenity)
        
        # Apply filters
        if amenity_type:
            query = query.filter(models.Amenity.amenity_type == amenity_type)
        if area_id:
            query = query.filter(models.Amenity.area_id == area_id)
        if status:
            query = query.filter(models.Amenity.status == status)
        
        # Apply pagination
        amenities = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        response_data = []
        spatial_service = SpatialService(db)
        
        for amenity in amenities:
            amenity_dict = {
                "amenity_id": amenity.amenity_id,
                "area_id": amenity.area_id,
                "name": amenity.name,
                "amenity_type": amenity.amenity_type,
                "description": amenity.description,
                "status": amenity.status,
                "capacity": amenity.capacity,
                "operating_hours": amenity.operating_hours,
                "contact_info": amenity.contact_info,
                "serves_areas": amenity.serves_areas,
                "service_radius_km": amenity.service_radius_km,
                "portal_id": amenity.portal_id,
                "created_at": amenity.created_at,
                "updated_at": amenity.updated_at,
                "geometry": spatial_service.geometry_to_geojson(amenity.geometry)
            }
            response_data.append(amenity_dict)
        
        log_api_response("get_amenities", {"count": len(response_data)})
        return response_data
        
    except Exception as e:
        log_error(e, "get_amenities")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving amenities: {str(e)}"
        )


@router.post("/sync", response_model=schemas.PortalSyncResponse)
async def sync_portal_data(
    request: schemas.CSIDCDataRequest,
    force_refresh: bool = Query(False, description="Force refresh from portal"),
    db: Session = Depends(get_db),
    csidc_service: CSIDCPortalService = Depends(get_csidc_service)
):
    """
    Synchronize data from CSIDC portal
    """
    try:
        log_api_request("sync_portal_data", {"area_type": request.area_type, "force_refresh": force_refresh})
        
        # Check recent sync
        if not force_refresh:
            recent_sync = db.query(models.PortalSync).filter(
                models.PortalSync.area_type == request.area_type,
                models.PortalSync.status == "success"
            ).order_by(models.PortalSync.sync_timestamp.desc()).first()
            
            if recent_sync and (datetime.now() - recent_sync.sync_timestamp).total_seconds() < 3600:
                # Return recent sync if less than 1 hour old
                return recent_sync
        
        # Create sync record
        sync_record = models.PortalSync(
            area_type=request.area_type,
            status="running",
            initiated_by="API"
        )
        db.add(sync_record)
        db.commit()
        db.refresh(sync_record)
        
        try:
            # Fetch data from portal
            async with csidc_service as service:
                portal_data = await service.fetch_area_data(
                    request.area_type.value,
                    request.bbox
                )
            
            # Process and store data
            records_created = 0
            records_updated = 0
            records_failed = 0
            spatial_service = SpatialService(db)
            
            for feature in portal_data.get('features', []):
                try:
                    props = feature.get('properties', {})
                    geometry = feature.get('geometry')
                    
                    if not geometry:
                        records_failed += 1
                        continue
                    
                    # Check if area exists
                    existing_area = None
                    if props.get('portal_id'):
                        existing_area = db.query(models.CSIDCArea).filter(
                            models.CSIDCArea.portal_id == props['portal_id']
                        ).first()
                    
                    if existing_area:
                        # Update existing
                        existing_area.name = props.get('name', existing_area.name)
                        existing_area.status = props.get('status', existing_area.status)
                        existing_area.size_hectares = props.get('size_hectares', existing_area.size_hectares)
                        existing_area.last_updated_portal = datetime.now()
                        records_updated += 1
                    else:
                        # Create new
                        new_area = models.CSIDCArea(
                            name=props.get('name', 'Unknown Area'),
                            area_type=request.area_type,
                            status=props.get('status', 'operational'),
                            size_hectares=props.get('size_hectares'),
                            district=props.get('district'),
                            authority=props.get('authority'),
                            portal_id=props.get('portal_id'),
                            geometry=spatial_service.geojson_to_geometry(geometry),
                            last_updated_portal=datetime.now()
                        )
                        db.add(new_area)
                        records_created += 1
                        
                except Exception as feature_error:
                    logger.error(f"Error processing feature: {feature_error}")
                    records_failed += 1
            
            # Update sync record
            sync_record.status = "success"
            sync_record.records_fetched = len(portal_data.get('features', []))
            sync_record.records_created = records_created
            sync_record.records_updated = records_updated
            sync_record.records_failed = records_failed
            
            db.commit()
            
            log_api_response("sync_portal_data", {
                "sync_id": sync_record.sync_id,
                "created": records_created,
                "updated": records_updated
            })
            
            return sync_record
            
        except Exception as sync_error:
            # Update sync record with error
            sync_record.status = "failed"
            sync_record.error_message = str(sync_error)
            db.commit()
            raise sync_error
            
    except Exception as e:
        log_error(e, "sync_portal_data")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing portal data: {str(e)}"
        )


@router.get("/statistics", response_model=schemas.CSIDCPortalStats)
async def get_csidc_statistics(
    db: Session = Depends(get_db)
):
    """
    Get CSIDC portal statistics and summary
    """
    try:
        log_api_request("get_csidc_statistics", {})
        
        # Industrial areas count by status
        industrial_query = db.query(models.CSIDCArea).filter(
            models.CSIDCArea.area_type.in_([
                models.CSIDCAreaType.INDUSTRIAL_AREA,
                models.CSIDCAreaType.OLD_INDUSTRIAL,
                models.CSIDCAreaType.DIRECTORATE_INDUSTRIAL
            ])
        )
        
        industrial_stats = {}
        for status in [s.value for s in schemas.AreaStatus]:
            count = industrial_query.filter(models.CSIDCArea.status == status).count()
            industrial_stats[status] = count
        
        # Land banks
        land_bank_query = db.query(models.CSIDCArea).filter(
            models.CSIDCArea.area_type == models.CSIDCAreaType.LAND_BANK
        )
        
        land_bank_stats = {}
        for status in [s.value for s in schemas.AreaStatus]:
            count = land_bank_query.filter(models.CSIDCArea.status == status).count()
            land_bank_stats[status] = count
        
        # Amenities
        amenity_stats = {}
        for amenity_type in [t.value for t in schemas.AmenityType]:
            count = db.query(models.Amenity).filter(
                models.Amenity.amenity_type == amenity_type
            ).count()
            amenity_stats[amenity_type] = count
        
        # Total area
        total_area = db.query(func.sum(models.CSIDCArea.size_hectares)).scalar() or 0
        
        # Districts
        districts = db.query(models.CSIDCArea.district.distinct()).filter(
            models.CSIDCArea.district.isnot(None)
        ).all()
        district_list = [d[0] for d in districts if d[0]]
        
        stats = {
            "industrial_areas": industrial_stats,
            "land_banks": land_bank_stats,
            "amenities": amenity_stats,
            "total_area_hectares": float(total_area),
            "districts": district_list,
            "last_updated": datetime.now()
        }
        
        log_api_response("get_csidc_statistics", {"total_areas": sum(industrial_stats.values())})
        return stats
        
    except Exception as e:
        log_error(e, "get_csidc_statistics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving CSIDC statistics: {str(e)}"
        )