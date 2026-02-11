"""
Spatial Analysis Service Module
Handles PostGIS spatial operations for geometric analysis
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from geoalchemy2 import functions as geo_func
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.ops import unary_union
from typing import Dict, Any, List, Tuple, Optional
import json

from ..database.models import Plot, Detection, Violation
from ..utils.logger import get_logger, log_error, log_database_query
from ..utils.config import settings

logger = get_logger(__name__)


class SpatialService:
    """
    Service class for PostGIS spatial operations
    Provides geometric analysis and spatial queries
    """
    
    def __init__(self, db: Session):
        """
        Initialize Spatial Service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def calculate_area(self, geometry: Dict[str, Any]) -> float:
        """
        Calculate area of a geometry in square meters (using geography type)
        
        Args:
            geometry: GeoJSON geometry
            
        Returns:
            Area in square meters
        """
        try:
            geom_wkt = self._geojson_to_wkt(geometry)
            
            query = text("""
                SELECT ST_Area(ST_GeomFromText(:geom_wkt, 4326)::geography)
            """)
            
            result = self.db.execute(query, {"geom_wkt": geom_wkt}).fetchone()
            area = result[0] if result else 0.0
            
            log_database_query("calculate_area", {"area_sq_m": area})
            return area
            
        except Exception as e:
            log_error(e, "calculate_area")
            return 0.0
    
    def calculate_area_hectares(self, geometry: Dict[str, Any]) -> float:
        """
        Calculate area in hectares
        """
        area_sqm = self.calculate_area(geometry)
        return area_sqm / 10000.0  # Convert to hectares
    
    def geometry_to_geojson(self, geom) -> Dict[str, Any]:
        """
        Convert PostGIS geometry to GeoJSON
        
        Args:
            geom: PostGIS geometry object
            
        Returns:
            GeoJSON geometry dictionary
        """
        try:
            if geom is None:
                return None
            
            # Convert to Shapely geometry
            shapely_geom = to_shape(geom)
            
            # Convert to GeoJSON
            return mapping(shapely_geom)
            
        except Exception as e:
            log_error(e, "geometry_to_geojson")
            return None
    
    def geojson_to_geometry(self, geojson: Dict[str, Any]):
        """
        Convert GeoJSON to PostGIS geometry
        
        Args:
            geojson: GeoJSON geometry dictionary
            
        Returns:
            PostGIS geometry object
        """
        try:
            if geojson is None:
                return None
            
            # Convert to Shapely geometry
            shapely_geom = shape(geojson)
            
            # Convert to PostGIS geometry using from_shape with SRID
            return from_shape(shapely_geom, srid=settings.SRID)
            
        except Exception as e:
            log_error(e, "geojson_to_geometry")
            return None
    
    def find_intersecting_areas(
        self, 
        geometry: Dict[str, Any], 
        area_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find CSIDC areas that intersect with given geometry
        
        Args:
            geometry: GeoJSON geometry to check
            area_type: Optional filter by area type
            
        Returns:
            List of intersecting areas with intersection data
        """
        try:
            from ..database.models import CSIDCArea
            
            geom_wkt = self._geojson_to_wkt(geometry)
            
            query = self.db.query(CSIDCArea).filter(
                func.ST_Intersects(
                    CSIDCArea.geometry,
                    func.ST_GeomFromText(geom_wkt, settings.SRID)
                )
            )
            
            if area_type:
                query = query.filter(CSIDCArea.area_type == area_type)
            
            intersecting_areas = query.all()
            
            results = []
            for area in intersecting_areas:
                # Calculate intersection area
                intersection_query = text("""
                    SELECT 
                        ST_Area(ST_Intersection(
                            :area_geom::geometry,
                            ST_GeomFromText(:input_geom, :srid)
                        )::geography) as intersection_area,
                        ST_Area(:area_geom::geography) as total_area
                """)
                
                intersection_result = self.db.execute(intersection_query, {
                    "area_geom": area.geometry,
                    "input_geom": geom_wkt,
                    "srid": settings.SRID
                }).fetchone()
                
                intersection_area = intersection_result[0] if intersection_result else 0
                total_area = intersection_result[1] if intersection_result else 0
                overlap_percentage = (intersection_area / total_area * 100) if total_area > 0 else 0
                
                results.append({
                    "area_id": area.area_id,
                    "name": area.name,
                    "area_type": area.area_type.value,
                    "intersection_area_sqm": intersection_area,
                    "total_area_sqm": total_area,
                    "overlap_percentage": overlap_percentage,
                    "geometry": self.geometry_to_geojson(area.geometry)
                })
            
            log_database_query("find_intersecting_areas", {"count": len(results)})
            return results
            
        except Exception as e:
            log_error(e, "find_intersecting_areas")
            return []
    
    def calculate_buffer_zone(
        self, 
        geometry: Dict[str, Any], 
        buffer_distance_m: float
    ) -> Dict[str, Any]:
        """
        Create buffer zone around geometry
        
        Args:
            geometry: GeoJSON geometry
            buffer_distance_m: Buffer distance in meters
            
        Returns:
            GeoJSON geometry of buffer zone
        """
        try:
            geom_wkt = self._geojson_to_wkt(geometry)
            
            # Use geography for accurate distance calculation
            query = text("""
                SELECT ST_AsGeoJSON(
                    ST_Transform(
                        ST_Buffer(
                            ST_GeomFromText(:geom_wkt, :srid)::geography,
                            :buffer_distance
                        )::geometry,
                        :srid
                    )
                )
            """)
            
            result = self.db.execute(query, {
                "geom_wkt": geom_wkt,
                "srid": settings.SRID,
                "buffer_distance": buffer_distance_m
            }).fetchone()
            
            if result and result[0]:
                buffer_geojson = json.loads(result[0])
                log_database_query("calculate_buffer_zone", {"buffer_distance_m": buffer_distance_m})
                return buffer_geojson
            
            return None
            
        except Exception as e:
            log_error(e, "calculate_buffer_zone")
            return None
    
    def find_nearby_amenities(
        self,
        center_point: Dict[str, Any],
        search_radius_km: float,
        amenity_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find amenities within radius of a point
        
        Args:
            center_point: GeoJSON Point geometry
            search_radius_km: Search radius in kilometers
            amenity_types: Optional filter by amenity types
            
        Returns:
            List of nearby amenities with distance
        """
        try:
            from ..database.models import Amenity
            
            if center_point['type'] != 'Point':
                raise ValueError("center_point must be a Point geometry")
            
            coordinates = center_point['coordinates']
            search_radius_m = search_radius_km * 1000
            
            # Create query with distance calculation
            distance_query = func.ST_Distance(
                func.ST_GeomFromText(
                    f"POINT({coordinates[0]} {coordinates[1]})",
                    settings.SRID
                ).cast(Geography),
                Amenity.geometry.cast(Geography)
            )
            
            query = self.db.query(
                Amenity,
                distance_query.label('distance_m')
            ).filter(
                distance_query <= search_radius_m
            )
            
            if amenity_types:
                query = query.filter(Amenity.amenity_type.in_(amenity_types))
            
            # Order by distance
            query = query.order_by('distance_m')
            
            results = []
            for amenity, distance in query.all():
                results.append({
                    "amenity_id": amenity.amenity_id,
                    "name": amenity.name,
                    "amenity_type": amenity.amenity_type.value,
                    "description": amenity.description,
                    "distance_km": round(distance / 1000, 2),
                    "distance_m": round(distance, 1),
                    "contact_info": amenity.contact_info,
                    "operating_hours": amenity.operating_hours,
                    "geometry": self.geometry_to_geojson(amenity.geometry)
                })
            
            log_database_query("find_nearby_amenities", {
                "count": len(results),
                "radius_km": search_radius_km
            })
            return results
            
        except Exception as e:
            log_error(e, "find_nearby_amenities")
            return []
    
    def get_area_statistics(self, area_id: int) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for a CSIDC area
        
        Args:
            area_id: CSIDC area ID
            
        Returns:
            Dictionary containing area statistics
        """
        try:
            from ..database.models import CSIDCArea, Plot, Violation, DroneDataCollection
            
            # Get the area
            area = self.db.query(CSIDCArea).filter(CSIDCArea.area_id == area_id).first()
            if not area:
                return {}
            
            stats = {
                "area_id": area_id,
                "name": area.name,
                "area_type": area.area_type.value,
                "size_hectares": area.size_hectares
            }
            
            # Calculate total area using PostGIS
            area_sqm = self.calculate_area(self.geometry_to_geojson(area.geometry))
            stats["calculated_area_hectares"] = area_sqm / 10000
            
            # Count intersecting plots
            plots_query = self.db.query(Plot).filter(
                func.ST_Intersects(Plot.geometry, area.geometry)
            )
            stats["intersecting_plots"] = plots_query.count()
            
            # Count violations in the area
            violations_query = self.db.query(Violation).join(Plot).filter(
                func.ST_Intersects(Plot.geometry, area.geometry)
            )
            stats["total_violations"] = violations_query.count()
            stats["unresolved_violations"] = violations_query.filter(
                Violation.is_resolved == False
            ).count()
            
            # Drone survey data
            drone_surveys = self.db.query(DroneDataCollection).filter(
                DroneDataCollection.area_id == area_id
            ).count()
            stats["drone_surveys_conducted"] = drone_surveys
            
            # Nearby amenities count
            if area.area_type.value in ['industrial_area', 'land_bank']:
                center_point = self._get_centroid(area.geometry)
                if center_point:
                    nearby = self.find_nearby_amenities(center_point, 5.0)  # 5km radius
                    stats["nearby_amenities"] = len(nearby)
            
            log_database_query("get_area_statistics", {"area_id": area_id})
            return stats
            
        except Exception as e:
            log_error(e, "get_area_statistics")
            return {}
    
    def _get_centroid(self, geometry) -> Optional[Dict[str, Any]]:
        """Get centroid of geometry as GeoJSON Point"""
        try:
            query = text("""
                SELECT ST_AsGeoJSON(ST_Centroid(:geom))
            """)
            
            result = self.db.execute(query, {"geom": geometry}).fetchone()
            if result and result[0]:
                return json.loads(result[0])
            
            return None
            
        except Exception:
            return None
                SELECT ST_Area(ST_GeographyFromText(:geom_wkt))
            """)
            
            result = self.db.execute(query, {"geom_wkt": geom_wkt}).scalar()
            
            return float(result) if result else 0.0
            
        except Exception as e:
            log_error(e, "calculate_area")
            raise
    
    def check_containment(
        self,
        outer_geometry: Dict[str, Any],
        inner_geometry: Dict[str, Any]
    ) -> bool:
        """
        Check if inner geometry is completely contained within outer geometry
        Uses ST_Contains
        
        Args:
            outer_geometry: GeoJSON of outer boundary
            inner_geometry: GeoJSON of inner geometry
            
        Returns:
            True if contained, False otherwise
        """
        try:
            outer_wkt = self._geojson_to_wkt(outer_geometry)
            inner_wkt = self._geojson_to_wkt(inner_geometry)
            
            query = text("""
                SELECT ST_Contains(
                    ST_GeomFromText(:outer, 4326),
                    ST_GeomFromText(:inner, 4326)
                )
            """)
            
            result = self.db.execute(
                query,
                {"outer": outer_wkt, "inner": inner_wkt}
            ).scalar()
            
            return bool(result)
            
        except Exception as e:
            log_error(e, "check_containment")
            return False
    
    def check_intersection(
        self,
        geom1: Dict[str, Any],
        geom2: Dict[str, Any]
    ) -> bool:
        """
        Check if two geometries intersect
        Uses ST_Intersects
        
        Args:
            geom1: First GeoJSON geometry
            geom2: Second GeoJSON geometry
            
        Returns:
            True if geometries intersect
        """
        try:
            wkt1 = self._geojson_to_wkt(geom1)
            wkt2 = self._geojson_to_wkt(geom2)
            
            query = text("""
                SELECT ST_Intersects(
                    ST_GeomFromText(:wkt1, 4326),
                    ST_GeomFromText(:wkt2, 4326)
                )
            """)
            
            result = self.db.execute(
                query,
                {"wkt1": wkt1, "wkt2": wkt2}
            ).scalar()
            
            return bool(result)
            
        except Exception as e:
            log_error(e, "check_intersection")
            return False
    
    def calculate_difference(
        self,
        geom1: Dict[str, Any],
        geom2: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate geometric difference (geom1 - geom2)
        Uses ST_Difference
        
        Args:
            geom1: First GeoJSON geometry
            geom2: Second GeoJSON geometry (to subtract)
            
        Returns:
            GeoJSON of difference geometry, or None if empty
        """
        try:
            wkt1 = self._geojson_to_wkt(geom1)
            wkt2 = self._geojson_to_wkt(geom2)
            
            query = text("""
                SELECT ST_AsGeoJSON(
                    ST_Difference(
                        ST_GeomFromText(:wkt1, 4326),
                        ST_GeomFromText(:wkt2, 4326)
                    )
                )
            """)
            
            result = self.db.execute(
                query,
                {"wkt1": wkt1, "wkt2": wkt2}
            ).scalar()
            
            if result:
                return json.loads(result)
            return None
            
        except Exception as e:
            log_error(e, "calculate_difference")
            return None
    
    def calculate_union(
        self,
        geometries: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate union of multiple geometries
        Uses ST_Union
        
        Args:
            geometries: List of GeoJSON geometries
            
        Returns:
            GeoJSON of union geometry
        """
        try:
            if not geometries:
                return None
            
            # Convert to Shapely geometries
            shapely_geoms = [shape(geom) for geom in geometries]
            
            # Perform union
            union_geom = unary_union(shapely_geoms)
            
            # Convert back to GeoJSON
            return mapping(union_geom)
            
        except Exception as e:
            log_error(e, "calculate_union")
            return None
    
    def detect_encroachment(
        self,
        plot_id: str,
        detected_geometry: Dict[str, Any]
    ) -> Tuple[bool, float, Optional[Dict[str, Any]]]:
        """
        Detect encroachment (activity outside plot boundary)
        
        Args:
            plot_id: Plot identifier
            detected_geometry: Detected activity geometry (GeoJSON)
            
        Returns:
            Tuple of (has_encroachment, encroachment_area_sqm, encroachment_geometry)
        """
        try:
            # Get plot boundary
            plot = self.db.query(Plot).filter(Plot.plot_id == plot_id).first()
            
            if not plot:
                logger.warning(f"Plot {plot_id} not found")
                return (False, 0.0, None)
            
            # Convert plot geometry to GeoJSON
            plot_geom = self._postgis_to_geojson(plot.geometry)
            
            # Check if detected geometry is contained within plot
            is_contained = self.check_containment(plot_geom, detected_geometry)
            
            if is_contained:
                # No encroachment
                return (False, 0.0, None)
            
            # Calculate encroachment (detected - plot)
            encroachment_geom = self.calculate_difference(detected_geometry, plot_geom)
            
            if encroachment_geom:
                encroachment_area = self.calculate_area(encroachment_geom)
                
                logger.warning(
                    f"Encroachment detected for plot {plot_id}: "
                    f"{encroachment_area:.2f} sqm outside boundary"
                )
                
                return (True, encroachment_area, encroachment_geom)
            
            return (False, 0.0, None)
            
        except Exception as e:
            log_error(e, f"detect_encroachment for plot {plot_id}")
            return (False, 0.0, None)
    
    def calculate_overlap_percentage(
        self,
        geom1: Dict[str, Any],
        geom2: Dict[str, Any]
    ) -> float:
        """
        Calculate percentage of geom1 that overlaps with geom2
        
        Args:
            geom1: First geometry
            geom2: Second geometry
            
        Returns:
            Overlap percentage (0-100)
        """
        try:
            wkt1 = self._geojson_to_wkt(geom1)
            wkt2 = self._geojson_to_wkt(geom2)
            
            query = text("""
                SELECT 
                    ST_Area(
                        ST_Intersection(
                            ST_GeographyFromText(:wkt1),
                            ST_GeographyFromText(:wkt2)
                        )
                    ) / ST_Area(ST_GeographyFromText(:wkt1)) * 100
            """)
            
            result = self.db.execute(
                query,
                {"wkt1": wkt1, "wkt2": wkt2}
            ).scalar()
            
            return float(result) if result else 0.0
            
        except Exception as e:
            log_error(e, "calculate_overlap_percentage")
            return 0.0
    
    def find_nearby_plots(
        self,
        plot_id: str,
        distance_meters: float = 1000.0
    ) -> List[Dict[str, Any]]:
        """
        Find plots within specified distance
        Uses ST_DWithin
        
        Args:
            plot_id: Reference plot ID
            distance_meters: Search radius in meters
            
        Returns:
            List of nearby plot information
        """
        try:
            plot = self.db.query(Plot).filter(Plot.plot_id == plot_id).first()
            
            if not plot:
                return []
            
            query = text("""
                SELECT 
                    plot_id,
                    industry_name,
                    ST_Distance(
                        geometry::geography,
                        :ref_geom::geography
                    ) as distance_meters
                FROM plots
                WHERE 
                    plot_id != :plot_id
                    AND ST_DWithin(
                        geometry::geography,
                        :ref_geom::geography,
                        :distance
                    )
                ORDER BY distance_meters
            """)
            
            results = self.db.execute(
                query,
                {
                    "plot_id": plot_id,
                    "ref_geom": plot.geometry,
                    "distance": distance_meters
                }
            ).fetchall()
            
            nearby = [
                {
                    "plot_id": row[0],
                    "industry_name": row[1],
                    "distance_meters": float(row[2])
                }
                for row in results
            ]
            
            logger.info(f"Found {len(nearby)} plots within {distance_meters}m of {plot_id}")
            
            return nearby
            
        except Exception as e:
            log_error(e, f"find_nearby_plots for {plot_id}")
            return []
    
    def _geojson_to_wkt(self, geojson: Dict[str, Any]) -> str:
        """Convert GeoJSON to WKT string"""
        shapely_geom = shape(geojson)
        return shapely_geom.wkt
    
    def _postgis_to_geojson(self, postgis_geom) -> Dict[str, Any]:
        """Convert PostGIS geometry to GeoJSON"""
        shapely_geom = to_shape(postgis_geom)
        return mapping(shapely_geom)
    
    def get_plot_geometry_geojson(self, plot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get plot geometry as GeoJSON
        
        Args:
            plot_id: Plot identifier
            
        Returns:
            GeoJSON geometry or None
        """
        try:
            plot = self.db.query(Plot).filter(Plot.plot_id == plot_id).first()
            
            if not plot:
                return None
            
            return self._postgis_to_geojson(plot.geometry)
            
        except Exception as e:
            log_error(e, f"get_plot_geometry_geojson for {plot_id}")
            return None


def get_spatial_service(db: Session) -> SpatialService:
    """
    Factory function to create SpatialService instance
    
    Args:
        db: Database session
        
    Returns:
        SpatialService instance
    """
    return SpatialService(db)


if __name__ == "__main__":
    # Test spatial service
    print("Spatial Service module loaded successfully")
    print("PostGIS functions available:")
    print("- ST_Contains")
    print("- ST_Intersects")
    print("- ST_Area")
    print("- ST_Difference")
    print("- ST_Union")
    print("- ST_DWithin")
