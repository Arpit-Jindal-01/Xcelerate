"""
Quick Test Script - Tests Individual Components
Run this after verify_system.py passes
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test if all modules can be imported"""
    print("=" * 60)
    print("🧪 Testing Module Imports")
    print("=" * 60)
    
    tests = []
    
    # Test config
    try:
        from utils.config import settings
        print(f"✓ Config loaded: {settings.APP_NAME}")
        tests.append(True)
    except Exception as e:
        print(f"✗ Config error: {e}")
        tests.append(False)
    
    # Test logger
    try:
        from utils.logger import app_logger
        print("✓ Logger initialized")
        tests.append(True)
    except Exception as e:
        print(f"✗ Logger error: {e}")
        tests.append(False)
    
    # Test ML models
    try:
        from models.unet import UNet
        from models.siamese import SiameseCNN
        print("✓ ML models imported")
        tests.append(True)
    except Exception as e:
        print(f"✗ ML models error: {e}")
        tests.append(False)
    
    # Test services
    try:
        from services.rule_engine import RuleEngine, DetectionData
        print("✓ Rule engine imported")
        tests.append(True)
    except Exception as e:
        print(f"✗ Rule engine error: {e}")
        tests.append(False)
    
    return all(tests)

def test_ml_models():
    """Test ML model creation"""
    print("\n" + "=" * 60)
    print("🤖 Testing ML Models")
    print("=" * 60)
    
    try:
        import torch
        from models.unet import UNet
        from models.siamese import SiameseCNN
        
        # Test U-Net
        unet = UNet(n_channels=3, n_classes=1)
        test_input = torch.randn(1, 3, 256, 256)
        output = unet(test_input)
        print(f"✓ U-Net: Input {test_input.shape} → Output {output.shape}")
        
        # Test Siamese
        siamese = SiameseCNN()
        img1 = torch.randn(1, 3, 256, 256)
        img2 = torch.randn(1, 3, 256, 256)
        score = siamese(img1, img2)
        print(f"✓ Siamese CNN: Change score = {score.item():.3f}")
        
        return True
    except Exception as e:
        print(f"✗ ML test failed: {e}")
        return False

def test_rule_engine():
    """Test rule engine logic"""
    print("\n" + "=" * 60)
    print("⚖️ Testing Rule Engine")
    print("=" * 60)
    
    try:
        from services.rule_engine import RuleEngine, DetectionData
        
        engine = RuleEngine()
        
        # Test case 1: Encroachment
        data1 = DetectionData(
            plot_id="TEST_001",
            approved_area=10000.0,
            approved_land_use="industrial",
            has_encroachment=True,
            encroachment_area=500.0
        )
        result1 = engine.evaluate(data1)
        print(f"✓ Encroachment test: {result1.violation_type.value} ({result1.severity.value})")
        
        # Test case 2: Compliant
        data2 = DetectionData(
            plot_id="TEST_002",
            approved_area=10000.0,
            approved_land_use="industrial",
            has_encroachment=False,
            built_up_area=9000.0
        )
        result2 = engine.evaluate(data2)
        print(f"✓ Compliant test: {result2.violation_type.value}")
        
        return True
    except Exception as e:
        print(f"✗ Rule engine test failed: {e}")
        return False

def test_database_schema():
    """Test database models"""
    print("\n" + "=" * 60)
    print("🗄️ Testing Database Schema")
    print("=" * 60)
    
    try:
        from database import models
        
        print(f"✓ Plot model: {models.Plot.__tablename__}")
        print(f"✓ Detection model: {models.Detection.__tablename__}")
        print(f"✓ Violation model: {models.Violation.__tablename__}")
        print(f"✓ AnalysisJob model: {models.AnalysisJob.__tablename__}")
        
        return True
    except Exception as e:
        print(f"✗ Database schema test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n🔬 CSIDC System Component Tests\n")
    
    results = []
    
    results.append(("Module Imports", test_imports()))
    results.append(("ML Models", test_ml_models()))
    results.append(("Rule Engine", test_rule_engine()))
    results.append(("Database Schema", test_database_schema()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status:12} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n✓ All tests passed! System is functional.")
        print("\nReady to start backend server:")
        print("  cd backend")
        print("  python main.py")
    else:
        print("\n✗ Some tests failed. Check errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
