# CSIDC Industrial Land Monitoring and Violation Detection System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🛰️ **Production-ready AI-powered system for industrial land monitoring using satellite imagery, deep learning, and PostGIS spatial analysis.**

Designed for **Chhattisgarh State Industrial Development Corporation (CSIDC)** to detect:
- ✅ Encroachment
- ✅ Illegal Construction
- ✅ Unused Land
- ✅ Suspicious Changes

---

## 🌟 Features

### **Satellite Data Integration**
- **Google Earth Engine** with Sentinel-2 Harmonized (10m resolution)
- **Landsat 8/9 Thermal** data for heat signature detection
- Automated cloud masking and composite generation
- NDVI, NDBI indices computation

### **AI/ML Models**
- **U-Net** for built-up area segmentation
- **Siamese CNN** for temporal change detection
- PyTorch-based inference pipeline
- GPU-accelerated processing

### **Spatial Analysis**
- PostgreSQL + PostGIS for geometric operations
- ST_Contains, ST_Intersects, ST_Area, ST_Difference
- Encroachment detection algorithm
- Boundary violation analysis

### **Rule-Based Decision Engine**
- Hierarchical violation classification
- Explainable confidence scoring
- Automated severity assessment
- Actionable recommendations

### **Web Interface**
- Interactive Leaflet map visualization
- Real-time plot monitoring
- Color-coded violation status
- Satellite imagery overlay

---

## 📁 Project Structure

```
industrial-land-monitoring/
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── services/
│   │   ├── gee_service.py          # Google Earth Engine integration
│   │   ├── ml_service.py           # ML inference service
│   │   ├── spatial_service.py      # PostGIS spatial operations
│   │   └── rule_engine.py          # Violation detection logic
│   ├── models/
│   │   ├── unet.py                 # U-Net segmentation model
│   │   └── siamese.py              # Siamese CNN for change detection
│   ├── database/
│   │   ├── connection.py           # Database connection manager
│   │   ├── models.py               # SQLAlchemy models
│   │   └── schemas.py              # Pydantic schemas
│   └── utils/
│       ├── config.py               # Configuration management
│       └── logger.py               # Logging setup
├── frontend/
│   ├── index.html                  # Web interface
│   └── leaflet_map.js              # Map visualization logic
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
└── README.md                       # This file
```

---

## 🚀 Installation

### **Prerequisites**
- Python 3.9+
- PostgreSQL 13+ with PostGIS 3.3+
- Google Earth Engine account
- (Optional) NVIDIA GPU with CUDA for ML acceleration

### **1. Clone Repository**
```bash
git clone https://github.com/your-org/industrial-land-monitoring.git
cd industrial-land-monitoring
```

### **2. Install Python Dependencies**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### **3. Setup PostgreSQL + PostGIS**
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

### **4. Configure Environment Variables**
```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `GEE_PROJECT_ID`: Google Earth Engine project ID
- `GEE_SERVICE_ACCOUNT`: GEE service account email
- `GEE_PRIVATE_KEY_PATH`: Path to GEE JSON key file

### **5. Authenticate Google Earth Engine**
```bash
# Install earthengine-api
pip install earthengine-api

# Authenticate (one-time setup)
earthengine authenticate

# Or use service account (production)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gee-key.json"
```

### **6. Initialize Database**
```bash
cd backend
python -c "from database.connection import create_tables; create_tables()"
```

---

## 🏃 Running the Application

### **Backend (FastAPI)**
```bash
cd backend
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### **Frontend**
```bash
cd frontend

# Serve with Python
python -m http.server 8080

# Or use any static file server
# npx serve .
```

Open browser: http://localhost:8080

---

## 📡 API Endpoints

### **Satellite Data**
```http
GET /api/v1/satellite?plot_id=PLOT_001&start_date=2024-01-01&end_date=2024-03-31
```
Returns Sentinel-2 RGB, NDVI, NDBI, and Landsat thermal data.

### **Plot Analysis**
```http
POST /api/v1/analyze/{plot_id}
```
Comprehensive analysis: satellite + ML + spatial + rule engine.

### **Violations**
```http
GET /api/v1/violations/{plot_id}
GET /api/v1/violations?violation_type=encroachment&severity=high
```

### **GeoJSON**
```http
GET /api/v1/geojson/{plot_id}
GET /api/v1/geojson/all
```
Returns plot boundaries and violation overlays.

---

## 🧪 Testing

### **Test Database Connection**
```bash
cd backend
python database/connection.py
```

### **Test GEE Service**
```bash
python services/gee_service.py
```

### **Test ML Models**
```bash
python models/unet.py
python models/siamese.py
```

### **Test Rule Engine**
```bash
python services/rule_engine.py
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
