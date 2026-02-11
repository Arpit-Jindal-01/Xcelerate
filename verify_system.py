"""
System Verification Script
Checks if all components are properly installed and configured
"""

import sys
import os
from pathlib import Path

def print_status(message, status):
    """Print colored status message"""
    symbols = {"success": "✓", "error": "✗", "warning": "⚠"}
    colors = {"success": "\033[92m", "error": "\033[91m", "warning": "\033[93m"}
    reset = "\033[0m"
    
    symbol = symbols.get(status, "•")
    color = colors.get(status, "")
    print(f"{color}{symbol}{reset} {message}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", "success")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor} (Need 3.9+)", "error")
        return False

def check_file_structure():
    """Check if all required files exist"""
    print("\n📁 Checking File Structure:")
    
    required_files = [
        "backend/main.py",
        "backend/services/gee_service.py",
        "backend/services/ml_service.py",
        "backend/services/spatial_service.py",
        "backend/services/rule_engine.py",
        "backend/models/unet.py",
        "backend/models/siamese.py",
        "backend/database/connection.py",
        "backend/database/models.py",
        "backend/database/schemas.py",
        "backend/utils/config.py",
        "backend/utils/logger.py",
        "frontend/index.html",
        "frontend/leaflet_map.js",
        "requirements.txt",
        ".env.example"
    ]
    
    all_exist = True
    for file_path in required_files:
        exists = Path(file_path).exists()
        status = "success" if exists else "error"
        print_status(f"{file_path}", status)
        if not exists:
            all_exist = False
    
    return all_exist

def check_packages():
    """Check if required packages are installed"""
    print("\n📦 Checking Python Packages:")
    
    packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "geoalchemy2",
        "torch",
        "numpy",
        "rasterio",
        "geopandas",
        "shapely",
        "loguru",
        "pydantic"
    ]
    
    all_installed = True
    for package in packages:
        try:
            __import__(package)
            print_status(f"{package}", "success")
        except ImportError:
            print_status(f"{package} (NOT INSTALLED)", "error")
            all_installed = False
    
    return all_installed

def check_env_file():
    """Check if .env file exists"""
    print("\n⚙️ Checking Configuration:")
    
    if Path(".env").exists():
        print_status(".env file exists", "success")
        return True
    else:
        print_status(".env file missing (copy from .env.example)", "warning")
        return False

def check_database():
    """Check database connection"""
    print("\n🗄️ Checking Database Connection:")
    
    try:
        from backend.database.connection import check_db_connection
        if check_db_connection():
            print_status("Database connection successful", "success")
            return True
        else:
            print_status("Database connection failed", "error")
            return False
    except Exception as e:
        print_status(f"Cannot test database: {str(e)}", "warning")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("🔍 CSIDC System Verification")
    print("=" * 60)
    
    print("\n🐍 Checking Python Version:")
    python_ok = check_python_version()
    
    files_ok = check_file_structure()
    packages_ok = check_packages()
    env_ok = check_env_file()
    
    # Database check is optional
    try:
        db_ok = check_database()
    except:
        db_ok = False
        print_status("Database check skipped (not configured)", "warning")
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("=" * 60)
    
    if python_ok and files_ok and packages_ok:
        print_status("System is ready for testing!", "success")
        print("\nNext steps:")
        print("1. Configure .env file with your credentials")
        print("2. Setup PostgreSQL database")
        print("3. Run: cd backend && python main.py")
        print("4. Open: http://localhost:8000/docs")
        return True
    else:
        print_status("System has configuration issues", "error")
        print("\nPlease fix the errors above before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
