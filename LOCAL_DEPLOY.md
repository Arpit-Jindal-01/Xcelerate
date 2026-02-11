# CSIDC Industrial Land Monitoring System
# Local Deployment & Testing Guide

## 🚀 Quick Verification & Deployment

### Step 1: Verify System Installation
```powershell
# Check if all components are in place
python verify_system.py
```

This will check:
- ✓ Python version (3.9+)
- ✓ All source files exist
- ✓ Required packages installed
- ✓ Configuration files present

### Step 2: Install Dependencies (if not already done)
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Test Components
```powershell
# Test individual modules without database
python test_components.py
```

This will test:
- ✓ Module imports
- ✓ ML models (U-Net, Siamese CNN)
- ✓ Rule engine logic
- ✓ Database schemas

### Step 4: Configure Environment (Optional for full deployment)
```powershell
# Copy environment template
copy .env.example .env

# Edit .env with your settings (optional for testing)
notepad .env
```

**Minimum for local testing:**
```ini
DATABASE_URL=postgresql://postgres:password@localhost:5432/csidc_monitoring
DEBUG=True
```

### Step 5: Start Backend (Without Database)
```powershell
cd backend
python main.py
```

**Backend starts at:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### Step 6: Start Frontend
Open a **new terminal**:
```powershell
cd frontend
python -m http.server 8080
```

**Frontend available at:** http://localhost:8080

---

## 🧪 Testing Without Full Setup

### Test 1: API Documentation
1. Start backend: `cd backend && python main.py`
2. Open: http://localhost:8000/docs
3. You should see all 8 endpoints documented

### Test 2: Health Check
```powershell
# Start backend, then in new terminal:
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {...}
}
```

### Test 3: ML Models (Standalone)
```powershell
cd backend
python models/unet.py
python models/siamese.py
```

Should output:
```
✓ U-Net test successful
✓ Siamese CNN test successful
```

### Test 4: Rule Engine (Standalone)
```powershell
cd backend
python services/rule_engine.py
```

Tests violation detection logic without database.

### Test 5: Frontend UI
1. Start frontend: `cd frontend && python -m http.server 8080`
2. Open: http://localhost:8080
3. Interface should load (will show "Backend not running" warnings - this is normal)

---

## 📂 What We've Built - File Inventory

### Backend Components (17 files)
```
backend/
├── main.py                          ← FastAPI app (8 endpoints)
├── services/
│   ├── __init__.py
│   ├── gee_service.py              ← Google Earth Engine
│   ├── ml_service.py               ← ML inference
│   ├── spatial_service.py          ← PostGIS operations
│   └── rule_engine.py              ← Violation logic
├── models/
│   ├── __init__.py
│   ├── unet.py                     ← U-Net (31M params)
│   └── siamese.py                  ← Siamese CNN (14M params)
├── database/
│   ├── __init__.py
│   ├── connection.py               ← DB connection pool
│   ├── models.py                   ← 4 tables (plots, detections, violations, jobs)
│   └── schemas.py                  ← API validation
└── utils/
    ├── __init__.py
    ├── config.py                   ← Settings management
    └── logger.py                   ← Structured logging
```

### Frontend (2 files)
```
frontend/
├── index.html                      ← Dashboard UI
└── leaflet_map.js                  ← Interactive map
```

### Configuration & Documentation (6 files)
```
├── requirements.txt                ← 40+ dependencies
├── .env.example                    ← Config template
├── .gitignore                      ← Git exclusions
├── README.md                       ← Full documentation
├── QUICKSTART.md                   ← Setup guide
└── LOCAL_DEPLOY.md                 ← This file
```

### Testing Scripts (2 files)
```
├── verify_system.py                ← System check
└── test_components.py              ← Component tests
```

**Total: 27 files, ~6,500 lines of production code**

---

## 🎯 What Works Without Database

✅ **API Documentation** - Fully browsable at /docs
✅ **ML Models** - Can run inference independently
✅ **Rule Engine** - Full violation detection logic
✅ **Frontend UI** - Complete interface loads
✅ **Configuration** - Settings management
✅ **Logging** - Structured logging system

❌ **Requires Database:**
- Saving/loading plots
- Storing detections
- Violation persistence
- GeoJSON endpoints

---

## 🗄️ Full Deployment with Database (Optional)

### 1. Install PostgreSQL + PostGIS
Download: https://www.postgresql.org/download/windows/

**Or use Docker:**
```powershell
docker run --name csidc-db -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgis/postgis:15-3.3
```

### 2. Create Database
```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE csidc_monitoring;
\c csidc_monitoring

-- Enable PostGIS
CREATE EXTENSION postgis;

-- Verify
SELECT PostGIS_Version();
```

### 3. Update .env
```ini
DATABASE_URL=postgresql://postgres:password@localhost:5432/csidc_monitoring
```

### 4. Initialize Database
```powershell
cd backend
python -c "from database.connection import create_tables; create_tables()"
```

### 5. Start Everything
```powershell
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
python -m http.server 8080
```

---

## 📊 Testing Checklist

- [ ] Run `python verify_system.py` - All checks pass
- [ ] Run `python test_components.py` - All tests pass
- [ ] Start backend - No errors, port 8000 listening
- [ ] Open http://localhost:8000/docs - Swagger UI loads
- [ ] Open http://localhost:8000/health - Returns JSON
- [ ] Start frontend - Port 8080 serving files
- [ ] Open http://localhost:8080 - Dashboard loads
- [ ] Check browser console - No critical errors

---

## 🔍 Troubleshooting

### "Module not found" errors
```powershell
pip install -r requirements.txt
```

### "Port already in use"
```powershell
# Change port in backend/utils/config.py
PORT=8001

# Or kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### "Cannot connect to database"
- Start PostgreSQL service
- Check DATABASE_URL in .env
- Verify credentials

### Frontend shows errors
- Ensure backend is running first
- Check API_BASE_URL in frontend/leaflet_map.js
- Open browser DevTools for details

---

## 📈 Next Steps After Local Testing

1. **Add Sample Data** - Import test plot boundaries
2. **Configure GEE** - Setup Google Earth Engine credentials
3. **Train Models** - Or use pretrained weights
4. **Run Analysis** - Test on real industrial plots
5. **Deploy to Cloud** - AWS/GCP/Azure production deployment

---

## 💡 Quick Demo (No Setup Required)

**See what we built by just running:**
```powershell
# 1. Check system
python verify_system.py

# 2. Test components
python test_components.py

# 3. View models
cd backend
python models/unet.py
python models/siamese.py

# 4. Test rule engine
python services/rule_engine.py
```

All of these work **without any configuration**!

---

## ✅ Success Indicators

**System is working if you see:**
- Backend: `Application startup complete` at http://localhost:8000
- Swagger: Interactive API docs at http://localhost:8000/docs
- Frontend: Dashboard loads at http://localhost:8080
- Tests: All component tests pass ✓

---

For issues or questions, check the main README.md or logs in `backend/logs/app.log`
