# CSIDC Industrial Land Monitoring System
# Quick Start Guide

## Development Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```sql
CREATE DATABASE csidc_monitoring;
\c csidc_monitoring
CREATE EXTENSION postgis;
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. Run Backend
```bash
cd backend
python main.py
```

### 5. Run Frontend
```bash
cd frontend
python -m http.server 8080
```

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Frontend
- Web Interface: http://localhost:8080

## Key Commands

### Test Database Connection
```bash
cd backend
python database/connection.py
```

### Test GEE Service
```bash
python services/gee_service.py
```

### Test ML Models
```bash
python models/unet.py
python models/siamese.py
```

## Directory Structure Created
✓ backend/main.py - FastAPI application
✓ backend/services/ - GEE, ML, Spatial, Rule Engine
✓ backend/models/ - U-Net, Siamese CNN
✓ backend/database/ - Models, Schemas, Connection
✓ backend/utils/ - Config, Logger
✓ frontend/ - HTML + Leaflet visualization
✓ requirements.txt
✓ .env.example
✓ README.md

## Next Steps

1. **Setup Google Earth Engine**
   - Create GEE project
   - Generate service account key
   - Update .env with credentials

2. **Train ML Models** (Optional)
   - Prepare training data
   - Train U-Net for built-up detection
   - Train Siamese CNN for change detection
   - Save weights to backend/models/weights/

3. **Populate Database**
   - Import plot boundaries (GeoJSON/Shapefile)
   - Add industry metadata
   - Set approved areas and land use types

4. **Run Analysis**
   - Select plot in frontend
   - Load satellite data
   - Run analysis
   - Review violations

## Troubleshooting

**Database Connection Error:**
- Check DATABASE_URL in .env
- Verify PostgreSQL is running
- Ensure PostGIS extension is enabled

**GEE Authentication Error:**
- Run: earthengine authenticate
- Or set service account credentials in .env

**ML Models Not Found:**
- Models will use random weights if pretrained weights not available
- This is normal for initial setup
- System will still function for testing

## Support
- GitHub: https://github.com/your-org/industrial-land-monitoring
- Email: support@csidc.gov.in
