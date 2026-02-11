# CSIDC Industrial Land Monitoring & Drone Survey System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🛰️ **Production-ready AI-powered system for industrial land monitoring using satellite imagery, deep learning, and CSIDC portal integration.**

Designed for **Chhattisgarh State Industrial Development Corporation (CSIDC)** to detect:
- ✅ Encroachment & Illegal Construction
- ✅ Unused Land & Suspicious Changes  
- ✅ Drone Survey Integration
- ✅ Real-time Portal Synchronization

## 🌟 Enhanced Features (Latest)

### **CSIDC Portal Integration** 🌐
- **Live Portal Sync** with https://cggis.cgstate.gov.in/csidc/
- **WFS/WMS Services** for geospatial data
- **Real-time Area Updates** from official CSIDC database
- **District-wise Filtering** (Raipur, Korba, Durg, Bilaspur)

### **Enhanced Web Interface** 🎨
- **Professional 4-Tab Interface**: Monitoring, CSIDC Areas, Drone Surveys, Analysis
- **Interactive Dashboard** with real-time statistics
- **CSIDC Portal Styling** with official color schemes
- **Responsive Design** optimized for all devices
- **Export Panel** with one-click downloads

### **Export Functionality** 📊
- **Multiple Formats**: GeoJSON, CSV, KML, Shapefile
- **Selective Export**: Choose Industrial Areas, Land Banks, Amenities
- **Instant Downloads** with proper file naming
- **GIS-Ready Data** for professional analysis

### **Drone Survey Management** 🚁
- **Survey Scheduling** and status tracking
- **Route Planning** with area coverage calculation
- **Data Integration** with satellite imagery
- **Violation Verification** through drone imagery

### **Core AI/ML Features** 🤖
- **U-Net** for built-up area segmentation
- **Siamese CNN** for temporal change detection
- **PyTorch-based** inference pipeline
- **GPU-accelerated** processing

### **Spatial Analysis** 🗺️
- **PostgreSQL + PostGIS** for geometric operations
- **ST_Contains, ST_Intersects** boundary analysis
- **Encroachment Detection** algorithm
- **Area Calculation** and change monitoring

### **Satellite Data Integration** 🛰️
- **Google Earth Engine** with Sentinel-2 Harmonized (10m resolution)
- **Landsat 8/9 Thermal** data for heat signature detection
- **Automated Cloud Masking** and composite generation
- **NDVI, NDBI Indices** computation

---

## 🚀 Quick Start (Demo Mode)

### **Instant Setup - No Database Required!**
```bash
# 1. Install basic dependencies
pip install fastapi uvicorn

# 2. Run demo application
python demo_app.py

# 3. Open browser
# http://localhost:8000
```

**Demo includes:**
- ✅ Working CSIDC portal interface
- ✅ Sample areas from Raipur, Korba, Durg, Bilaspur
- ✅ Export functionality (GeoJSON, CSV, KML)
- ✅ Interactive maps with professional styling

---

## 📁 Enhanced Project Structure

```
xcelerate/
├── demo_app.py                     # 🚀 MAIN DEMO APPLICATION (Quick start)
├── frontend/
│   ├── index.html                  # 🎨 Enhanced CSIDC Portal Interface
│   ├── index_backup.html           # Original backup
│   └── leaflet_map.js              # Map visualization logic
├── backend/                        # 🏗️ Full Enterprise Backend
│   ├── main.py                     # Enhanced FastAPI application
│   ├── api/                        # 🆕 NEW API MODULES
│   │   ├── csidc_router.py         # CSIDC areas management
│   │   └── drone_router.py         # Drone survey operations
│   ├── services/
│   │   ├── csidc_service.py        # 🆕 CSIDC portal integration
│   │   ├── gee_service.py          # Google Earth Engine
│   │   ├── ml_service.py           # ML inference service
│   │   ├── spatial_service.py      # Enhanced PostGIS operations
│   │   └── rule_engine.py          # Violation detection logic
│   ├── models/
│   │   ├── unet.py                 # U-Net segmentation model
│   │   └── siamese.py              # Siamese CNN for change detection
│   ├── database/
│   │   ├── connection.py           # Database connection manager
│   │   ├── models.py               # 🆕 Enhanced SQLAlchemy models
│   │   └── schemas.py              # 🆕 Enhanced Pydantic schemas
│   └── utils/
│       ├── config.py               # Configuration management
│       └── logger.py               # Logging setup
├── exports/                        # 🆕 Export files directory
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
└── README.md                       # This file
```

---

## 🚀 Installation

### **Quick Demo Setup (No Dependencies)**
```bash
# 1. Clone repository
git clone https://github.com/Arpit-Jindal-01/Xcelerate.git
cd xcelerate

# 2. Install minimal requirements
pip install fastapi uvicorn

# 3. Run demo (includes sample CSIDC data)
python demo_app.py

# 4. Open browser
open http://localhost:8000
```

### **Full Enterprise Setup (Advanced)**

#### **Prerequisites**
- Python 3.9+
- PostgreSQL 13+ with PostGIS 3.3+
- Google Earth Engine account
- (Optional) NVIDIA GPU with CUDA for ML acceleration

#### **1. Install Python Dependencies**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

#### **2. Setup PostgreSQL + PostGIS**
```sql
-- Create database
CREATE DATABASE csidc_monitoring;

-- Connect to database
\c csidc_monitoring

-- Enable PostGIS
CREATE EXTENSION postgis;

-- Create user
CREATE USER csidc_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE csidc_monitoring TO csidc_user;
```

#### **3. Configure Environment Variables**
```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `CSIDC_PORTAL_URL`: https://cggis.cgstate.gov.in/csidc/
- `GEE_PROJECT_ID`: Google Earth Engine project ID
- `GEE_SERVICE_ACCOUNT`: GEE service account email
- `GEE_PRIVATE_KEY_PATH`: Path to GEE JSON key file

#### **4. Initialize Database**
```bash
cd backend
python -c "from database.connection import create_tables; create_tables()"
```
```bash
cd backend
python -c "from database.connection import create_tables; create_tables()"
```

---

## 🏃 Running the Application

### **Option 1: Demo Mode (Recommended for Quick Start)**
```bash
# Install minimal dependencies
pip install fastapi uvicorn

# Run demo application
python demo_app.py

# Access application
open http://localhost:8000
```

### **Option 2: Full Backend (Enterprise Setup)**
```bash
# Install all dependencies
pip install -r requirements.txt

# Run full backend
cd backend
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **Available URLs:**
- **🌐 Main Interface**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/api/docs  
- **📖 ReDoc**: http://localhost:8000/api/redoc
- **💚 Health Check**: http://localhost:8000/api/health

### **Frontend Features:**
- **4 Main Tabs**: Monitoring, CSIDC Areas, Drone Surveys, Analysis
- **Interactive Maps** with Leaflet and CSIDC styling
- **Export Panel** for data downloads
- **Real-time Statistics** dashboard
- **Responsive Design** for mobile/desktop

---

## 📡 Enhanced API Endpoints

### **CSIDC Portal Integration**
```http
GET /api/v1/csidc/areas                    # Get all CSIDC areas
GET /api/v1/csidc/areas?district=Raipur    # Filter by district
GET /api/v1/csidc/areas/{area_id}         # Get specific area details
POST /api/v1/csidc/sync                   # Sync with CSIDC portal
```

### **Drone Survey Operations**
```http
GET /api/v1/drone/surveys                 # Get all surveys
POST /api/v1/drone/surveys                # Create new survey
GET /api/v1/drone/surveys?area_id=1       # Filter by area
```

### **Export & Download**
```http
POST /api/v1/quick-export                 # Quick data export
GET /api/v1/reports/export?format=geojson # Formatted export
```

### **System & Analysis**
```http
GET /api/health                           # System health check
GET /api/v1/statistics                    # Dashboard statistics
POST /api/v1/analysis/satellite           # Satellite analysis
POST /api/v1/analysis/ai                  # AI model analysis
```

### **Legacy Endpoints** (Full Backend)
```http
GET /api/v1/satellite?plot_id=PLOT_001    # Satellite data
POST /api/v1/analyze/{plot_id}            # Comprehensive analysis
GET /api/v1/violations/{plot_id}          # Violations
GET /api/v1/geojson/{plot_id}             # GeoJSON data
```

---

## 🧪 Testing

### **Demo Application Tests**
```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test CSIDC areas
curl http://localhost:8000/api/v1/csidc/areas

# Test export functionality
curl -X POST "http://localhost:8000/api/v1/quick-export" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "industrial_areas=true&format=geojson" \
  --output test_export.geojson
```

### **Frontend Integration Tests**
```bash
# Test frontend serves correctly
curl http://localhost:8000

# Test API documentation
curl http://localhost:8000/api/docs
```

### **Full Backend Tests** (Enterprise mode)
```bash
# Test Database Connection
cd backend
python database/connection.py

# Test CSIDC Service  
python services/csidc_service.py

# Test GEE Service
python services/gee_service.py

# Test ML Models
python models/unet.py
python models/siamese.py

# Test Rule Engine
python services/rule_engine.py
```

### **Component Verification**
```bash
# Verify all components
python verify_system.py

# Test individual components
python test_components.py
```

---

## 🤖 Machine Learning Models

### **U-Net (Built-up Detection)**
- **Input**: 3-channel RGB satellite image (256×256)
- **Output**: Binary segmentation mask
- **Architecture**: Encoder-decoder with skip connections
- **Parameters**: ~31M
- **Training**: Sentinel-2 imagery with annotated built-up areas

### **Siamese CNN (Change Detection)**
- **Input**: Two temporal images (T1, T2)
- **Output**: Change probability score (0-1)
- **Architecture**: Shared CNN backbone + classification head
- **Parameters**: ~14M
- **Training**: Temporal image pairs with change labels

### **Pre-trained Weights**
Place pretrained weights in `backend/models/weights/`:
- `unet_builtup_v1.pth`
- `siamese_change_v1.pth`

---

## 🗄️ Database Schema

### **Tables**
1. **plots**: Industrial plot boundaries and metadata
2. **detections**: ML detection results (built-up, heat, change)
3. **violations**: Detected violations with recommendations
4. **analysis_jobs**: Batch processing jobs

### **Key Spatial Operations**
```sql
-- Check encroachment
SELECT ST_Difference(detected_geom, plot_boundary) AS encroachment;

-- Calculate built-up area
SELECT ST_Area(detected_builtup::geography) / ST_Area(plot_boundary::geography) AS ratio;

-- Find nearby plots
SELECT * FROM plots WHERE ST_DWithin(geometry::geography, ref_point::geography, 1000);
```

---

## 🎨 Visualization

### **Violation Color Coding**
- 🔴 **Red**: Encroachment (Critical)
- 🟠 **Orange**: Illegal Construction (High)
- 🟡 **Yellow**: Unused Land (Low)
- 🔵 **Blue**: Suspicious Change (Medium)
- 🟢 **Green**: Compliant

### **Map Layers**
- Base: OpenStreetMap
- Plots: Color-coded polygons
- Satellite: RGB composite overlay
- Thermal: Heat signature overlay
- Violations: Evidence geometry

---

## 🔧 Configuration

### **Detection Thresholds** (in `.env`)
```ini
ENCROACHMENT_THRESHOLD=0.01           # 1% outside boundary → violation
ILLEGAL_CONSTRUCTION_THRESHOLD=1.10   # 110% of approved area → violation
UNUSED_LAND_HEATMAP_THRESHOLD=0.05    # <5% heat signature → unused
CHANGE_DETECTION_THRESHOLD=0.70       # >70% confidence → suspicious
```

### **Satellite Parameters**
```python
SENTINEL_CLOUD_THRESHOLD = 20         # Max 20% cloud cover
SENTINEL_SCALE = 10                   # 10m resolution
LANDSAT_SCALE = 30                    # 30m resolution
```

---

## 📊 Monitoring Dashboard

Access real-time statistics:
- Total plots monitored
- Active violations
- Violation breakdown by type/severity
- Recent detections
- Compliance percentage

---

## 🚢 Deployment

### **Docker** (Coming Soon)
```bash
docker-compose up --build
```

### **Cloud Deployment**
- **Backend**: AWS EC2 / Google Cloud Run / Azure App Service
- **Database**: AWS RDS PostgreSQL with PostGIS
- **ML Models**: GPU instance (AWS p3, GCP n1-highmem)
- **Frontend**: AWS S3 + CloudFront / Netlify

### **Scalability Considerations**
- Connection pooling (SQLAlchemy)
- Background task queue (Celery + Redis)
- Batch processing for large plots
- Caching layer (Redis)
- Load balancing (Nginx)

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 👥 Authors

**CSIDC Development Team**
- 📧 Email: monitoring@csidc.gov.in
- 🌐 Website: https://csidc.gov.in

---

## 🙏 Acknowledgments

- Google Earth Engine for satellite data access
- Sentinel-2 and Landsat programs
- FastAPI and PyTorch communities
- OpenStreetMap contributors

---

## 📞 Support

For issues or questions:
- 📋 GitHub Issues: [Create Issue](https://github.com/your-org/industrial-land-monitoring/issues)
- 📧 Email: support@csidc.gov.in
- 📖 Documentation: [Wiki](https://github.com/your-org/industrial-land-monitoring/wiki)

---

**Built with ❤️ for sustainable industrial development**
