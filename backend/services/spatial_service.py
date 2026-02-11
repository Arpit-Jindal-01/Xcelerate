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
