"""
Simple CSIDC Demo Application  
Industrial Land Monitoring Demo without complex geo dependencies
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, StreamingResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
import io
import csv
import tempfile
import zipfile

# Initialize FastAPI app
app = FastAPI(
    title="CSIDC Industrial Land Monitoring Demo",
    version="1.0.0",
    description="Demonstration of CSIDC portal integration and monitoring capabilities",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
MOCK_AREAS = [
    {
        "area_id": 1,
        "name": "Raipur Industrial Area",
        "area_type": "industrial_area",
        "status": "operational",
        "size_hectares": 1250.5,
        "district": "Raipur",
        "authority": "CSIDC",
        "sync_status": "synced",
        "last_sync": "2024-01-15T10:30:00Z",
        "coordinates": [[81.63, 21.25], [81.68, 21.25], [81.68, 21.20], [81.63, 21.20]]
    },
    {
        "area_id": 2,
        "name": "Korba Land Bank",
        "area_type": "land_bank",
        "status": "available",
        "size_hectares": 850.2,
        "district": "Korba",
        "authority": "CSIDC",
        "sync_status": "synced",
        "last_sync": "2024-01-15T10:30:00Z",
        "coordinates": [[82.65, 22.35], [82.72, 22.35], [82.72, 22.30], [82.65, 22.30]]
    },
    {
        "area_id": 3,
        "name": "Durg Manufacturing Zone",
        "area_type": "industrial_area", 
        "status": "operational",
        "size_hectares": 625.8,
        "district": "Durg",
        "authority": "CSIDC",
        "sync_status": "synced",
        "last_sync": "2024-01-15T10:30:00Z",
        "coordinates": [[81.28, 21.19], [81.33, 21.19], [81.33, 21.15], [81.28, 21.15]]
    },
    {
        "area_id": 4,
        "name": "Bilaspur Land Bank",
        "area_type": "land_bank",
        "status": "available",
        "size_hectares": 1180.3,
        "district": "Bilaspur",
        "authority": "CSIDC",
        "sync_status": "synced",
        "last_sync": "2024-01-15T10:30:00Z",
        "coordinates": [[82.15, 22.08], [82.22, 22.08], [82.22, 22.02], [82.15, 22.02]]
    }
]

MOCK_SURVEYS = [
    {
        "survey_id": 1,
        "area_id": 1,
        "survey_type": "routine",
        "date_conducted": "2024-01-12T09:00:00Z",
        "operator": "CSIDC Survey Team A",
        "status": "completed",
        "findings": "No violations detected",
        "area_covered_hectares": 125.5
    },
    {
        "survey_id": 2,
        "area_id": 2,
        "survey_type": "violation_check",
        "date_conducted": "2024-01-10T14:30:00Z",
        "operator": "CSIDC Survey Team B",
        "status": "completed",
        "findings": "Unauthorized construction detected in sector 3",
        "area_covered_hectares": 85.2
    }
]

# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML file"""
    try:
        # Get the absolute path to the frontend file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_path = os.path.join(current_dir, "frontend", "index.html")
        
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError as e:
        return HTMLResponse(content=f"""
        <html>
            <head><title>CSIDC Demo</title></head>
            <body>
                <h1>CSIDC Industrial Land Monitoring Demo</h1>
                <p>Frontend not found at expected path. Please access the API at <a href="/api/docs">/api/docs</a></p>
                <p>Error: {str(e)}</p>
            </body>
        </html>
        """)

# Health check
@app.get("/api/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "csidc_portal": "connected",
            "database": "operational",
            "ai_models": "loaded"
        }
    }

# Statistics endpoint
@app.get("/api/v1/statistics")
async def get_statistics():
    """Get system statistics"""
    return {
        "total_areas": len(MOCK_AREAS),
        "industrial_areas": len([a for a in MOCK_AREAS if a["area_type"] == "industrial_area"]),
        "land_banks": len([a for a in MOCK_AREAS if a["area_type"] == "land_bank"]),
        "total_surveys": len(MOCK_SURVEYS),
        "recent_surveys": len([s for s in MOCK_SURVEYS if datetime.fromisoformat(s["date_conducted"].replace("Z", "+00:00")) > datetime.now() - timedelta(days=30)]),
        "compliance_rate": 94.2,
        "violation_rate": 5.8,
        "last_updated": datetime.now().isoformat()
    }

# CSIDC Areas endpoints
@app.get("/api/v1/csidc/areas")
async def get_csidc_areas(district: str = None, area_type: str = None):
    """Get CSIDC areas with optional filtering"""
    areas = MOCK_AREAS
    
    if district:
        areas = [a for a in areas if a["district"].lower() == district.lower()]
    if area_type:
        areas = [a for a in areas if a["area_type"] == area_type]
    
    return {
        "areas": areas,
        "total_count": len(areas),
        "filters": {
            "district": district,
            "area_type": area_type
        }
    }

@app.get("/api/v1/csidc/areas/{area_id}")
async def get_area_details(area_id: int):
    """Get detailed information about a specific area"""
    area = next((a for a in MOCK_AREAS if a["area_id"] == area_id), None)
    if not area:
        return JSONResponse(
            status_code=404,
            content={"error": "Area not found"}
        )
    
    return {
        "area": area,
        "recent_surveys": [s for s in MOCK_SURVEYS if s["area_id"] == area_id],
        "compliance_history": [
            {"date": "2024-01-01", "score": 95.2},
            {"date": "2024-01-08", "score": 93.8},
            {"date": "2024-01-15", "score": 94.5}
        ]
    }

@app.post("/api/v1/csidc/sync")
async def sync_csidc_portal():
    """Simulate syncing with CSIDC portal"""
    return {
        "status": "success",
        "message": "Portal sync completed successfully",
        "areas_updated": len(MOCK_AREAS),
        "sync_timestamp": datetime.now().isoformat(),
        "next_sync": (datetime.now() + timedelta(hours=6)).isoformat()
    }

# Drone Survey endpoints
@app.get("/api/v1/drone/surveys")
async def get_drone_surveys(area_id: int = None, survey_type: str = None):
    """Get drone survey data with optional filtering"""
    surveys = MOCK_SURVEYS
    
    if area_id:
        surveys = [s for s in surveys if s["area_id"] == area_id]
    if survey_type:
        surveys = [s for s in surveys if s["survey_type"] == survey_type]
    
    return {
        "surveys": surveys,
        "total_count": len(surveys)
    }

@app.post("/api/v1/drone/surveys")
async def create_drone_survey(survey_data: Dict[str, Any]):
    """Create a new drone survey"""
    new_survey = {
        "survey_id": len(MOCK_SURVEYS) + 1,
        "area_id": survey_data.get("area_id"),
        "survey_type": survey_data.get("survey_type", "routine"),
        "date_conducted": datetime.now().isoformat(),
        "operator": survey_data.get("operator", "CSIDC Survey Team"),
        "status": "scheduled",
        "findings": "Survey in progress",
        "area_covered_hectares": survey_data.get("area_covered_hectares", 0)
    }
    
    MOCK_SURVEYS.append(new_survey)
    
    return {
        "status": "success",
        "message": "Drone survey created successfully",
        "survey": new_survey
    }

# Analysis endpoints
@app.post("/api/v1/analysis/satellite")
async def run_satellite_analysis(analysis_request: Dict[str, Any]):
    """Simulate satellite data analysis"""
    return {
        "status": "completed",
        "analysis_id": f"SAT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "area_analyzed": analysis_request.get("area_id", "all"),
        "detection_results": {
            "built_up_change": "+2.3%",
            "vegetation_loss": "-1.1%",
            "new_constructions": 3,
            "violations_detected": 0
        },
        "confidence_score": 0.92,
        "analysis_date": datetime.now().isoformat()
    }

@app.post("/api/v1/analysis/ai")
async def run_ai_analysis(analysis_request: Dict[str, Any]):
    """Simulate AI analysis"""
    return {
        "status": "completed",
        "analysis_id": f"AI_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "model_used": "Siamese CNN + U-Net",
        "area_analyzed": analysis_request.get("area_id", "all"),
        "detection_results": {
            "change_detection": "Normal patterns detected",
            "anomaly_score": 0.23,
            "violation_probability": 0.05,
            "recommendation": "Continue routine monitoring"
        },
        "processing_time_seconds": 45.2,
        "analysis_date": datetime.now().isoformat()
    }

@app.get("/api/v1/reports/export")
async def export_data(format: str = "geojson", include_surveys: bool = True):
    """Export data in various formats"""
    export_data = {
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "format": format,
            "total_areas": len(MOCK_AREAS),
            "total_surveys": len(MOCK_SURVEYS) if include_surveys else 0
        },
        "areas": MOCK_AREAS,
        "surveys": MOCK_SURVEYS if include_surveys else []
    }
    
    return {
        "status": "success",
        "download_url": f"/api/downloads/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
        "data": export_data
    }

@app.post("/api/v1/quick-export")
async def quick_export(
    industrial_areas: bool = True,
    land_banks: bool = True, 
    amenities: bool = False,
    violations: bool = False,
    format: str = "geojson"
):
    """Quick export functionality for the export panel"""
    
    # Filter data based on selections
    filtered_areas = []
    if industrial_areas:
        filtered_areas.extend([a for a in MOCK_AREAS if a["area_type"] == "industrial_area"])
    if land_banks:
        filtered_areas.extend([a for a in MOCK_AREAS if a["area_type"] == "land_bank"])
    if amenities:
        filtered_areas.extend([a for a in MOCK_AREAS if a["area_type"] == "amenity"])
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"csidc_export_{timestamp}"
    
    if format.lower() == "geojson":
        return await generate_geojson(filtered_areas, filename)
    elif format.lower() == "csv":
        return await generate_csv(filtered_areas, filename)
    elif format.lower() == "kml":
        return await generate_kml(filtered_areas, filename)
    else:
        return JSONResponse({"error": "Unsupported format"}, status_code=400)

async def generate_geojson(areas: List[Dict], filename: str):
    """Generate GeoJSON format export"""
    features = []
    for area in areas:
        if "coordinates" in area:
            if area["area_type"] == "amenity":
                # Point geometry for amenities
                geometry = {
                    "type": "Point",
                    "coordinates": area["coordinates"]
                }
            else:
                # Polygon geometry for areas
                geometry = {
                    "type": "Polygon", 
                    "coordinates": [area["coordinates"] + [area["coordinates"][0]]]  # Close polygon
                }
            
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "area_id": area["area_id"],
                    "name": area["name"],
                    "area_type": area["area_type"],
                    "status": area.get("status", ""),
                    "district": area.get("district", ""),
                    "size_hectares": area.get("size_hectares", 0),
                    "authority": area.get("authority", "")
                }
            }
            features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "source": "CSIDC Monitoring System",
            "total_features": len(features)
        },
        "features": features
    }
    
    # Create in-memory file
    content = json.dumps(geojson, indent=2)
    return StreamingResponse(
        io.StringIO(content),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}.geojson"}
    )

async def generate_csv(areas: List[Dict], filename: str):
    """Generate CSV format export"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Area ID", "Name", "Type", "Status", "District", 
        "Size (hectares)", "Authority", "Latitude", "Longitude"
    ])
    
    # Write data
    for area in areas:
        # Get centroid for location
        if "coordinates" in area:
            if area["area_type"] == "amenity":
                lat, lon = area["coordinates"][1], area["coordinates"][0]
            else:
                # Calculate polygon centroid
                coords = area["coordinates"]
                lat = sum(coord[1] for coord in coords) / len(coords)
                lon = sum(coord[0] for coord in coords) / len(coords)
        else:
            lat, lon = "", ""
            
        writer.writerow([
            area["area_id"],
            area["name"],
            area["area_type"],
            area.get("status", ""),
            area.get("district", ""),
            area.get("size_hectares", ""),
            area.get("authority", ""),
            lat,
            lon
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
    )

async def generate_kml(areas: List[Dict], filename: str):
    """Generate KML format export"""
    kml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>CSIDC Areas Export</name>
<description>Exported from CSIDC Monitoring System</description>
'''
    
    # Add styles
    kml_content += '''
<Style id="industrial">
  <PolyStyle><color>4d0000ff</color><fill>1</fill></PolyStyle>
  <LineStyle><color>ff0000ff</color><width>2</width></LineStyle>
</Style>
<Style id="landbank">
  <PolyStyle><color>4d00ff00</color><fill>1</fill></PolyStyle>
  <LineStyle><color>ff00ff00</color><width>2</width></LineStyle>
</Style>
'''
    
    for area in areas:
        if "coordinates" in area:
            kml_content += f'''
<Placemark>
  <name>{area["name"]}</name>
  <description><![CDATA[
    Type: {area["area_type"]}<br/>
    Status: {area.get("status", "")}<br/>
    District: {area.get("district", "")}<br/>
    Size: {area.get("size_hectares", "")} hectares
  ]]></description>
  <styleUrl>#{"industrial" if "industrial" in area["area_type"] else "landbank"}</styleUrl>
'''
            
            if area["area_type"] == "amenity":
                # Point
                lon, lat = area["coordinates"]
                kml_content += f'''
  <Point>
    <coordinates>{lon},{lat},0</coordinates>
  </Point>
'''
            else:
                # Polygon
                coords_str = " ".join([f"{coord[0]},{coord[1]},0" for coord in area["coordinates"]])
                kml_content += f'''
  <Polygon>
    <outerBoundaryIs>
      <LinearRing>
        <coordinates>{coords_str}</coordinates>
      </LinearRing>
    </outerBoundaryIs>
  </Polygon>
'''
            
            kml_content += "</Placemark>\n"
    
    kml_content += "</Document>\n</kml>"
    
    return StreamingResponse(
        io.StringIO(kml_content),
        media_type="application/vnd.google-earth.kml+xml",
        headers={"Content-Disposition": f"attachment; filename={filename}.kml"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)