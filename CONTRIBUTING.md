# Contributing to CSIDC Industrial Land Monitoring System

Thank you for contributing to the **Xcelerate Hackathon Project**! This guide will help you get started.

---

## 🎯 Project Vision

Build a production-ready AI-powered system for monitoring industrial land use and detecting violations using satellite imagery, machine learning, and geospatial analysis.

---

## 👥 Team Structure

### Core Team Members
- **Team Lead:** Project coordination and architecture
- **Backend Developers:** FastAPI, services, database
- **ML Engineers:** Model training and optimization
- **Frontend Developers:** UI/UX and visualization
- **DevOps Engineers:** Deployment and infrastructure

### Current Contributors
*Add your name when you make your first contribution:*

1. [Your Name] - Initial project setup

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Arpit-Jindal-01/Xcelerate.git
cd Xcelerate
```

### 2. Read Documentation
Before contributing, familiarize yourself with:
- [README.md](README.md) - Project overview
- [PROJECT_LOG.md](PROJECT_LOG.md) - Complete technical documentation
- [QUICKSTART.md](QUICKSTART.md) - Setup instructions

### 3. Set Up Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 4. Run Tests
```bash
python verify_system.py
python test_components.py
```

---

## 📝 How to Contribute

### Step 1: Pick an Issue
- Check [GitHub Issues](https://github.com/Arpit-Jindal-01/Xcelerate/issues)
- Look for labels: `good first issue`, `help wanted`, `enhancement`
- Comment on the issue to claim it

### Step 2: Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

**Branch Naming Convention:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical production fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding tests

### Step 3: Make Changes
- Write clean, documented code
- Follow existing code style
- Add comments for complex logic
- Update documentation if needed

### Step 4: Test Your Changes
```bash
# Run system verification
python verify_system.py

# Test specific components
cd backend
python models/unet.py  # If ML changes
python services/rule_engine.py  # If logic changes

# Start backend to test API
python main.py
```

### Step 5: Commit Changes
Use conventional commit messages:
```bash
git add .
git commit -m "feat(ml): add model training script"
# or
git commit -m "fix(api): resolve CORS issue on analyze endpoint"
# or
git commit -m "docs: update deployment instructions"
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

### Step 6: Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub:
1. Go to the repository
2. Click "New Pull Request"
3. Select your branch
4. Fill in PR template (see below)
5. Request review from team members

---

## 📋 Pull Request Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tested on local environment

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Closes #123
```

---

## 💻 Code Style Guidelines

### Python (Backend)

**Follow PEP 8:**
```python
# Good
def calculate_area(geometry: Dict[str, Any]) -> float:
    """
    Calculate area of geometry in square meters.
    
    Args:
        geometry: GeoJSON geometry
        
    Returns:
        Area in square meters
    """
    # Implementation
    pass

# Bad
def calc(g):
    # No docstring, unclear naming
    pass
```

**Type Hints:**
```python
# Always use type hints
from typing import Dict, List, Optional, Any

def process_data(data: List[Dict[str, Any]]) -> Optional[str]:
    pass
```

**Docstrings:**
```python
# Use Google-style docstrings
def my_function(param1: str, param2: int) -> bool:
    """
    Short description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input
    """
    pass
```

### JavaScript (Frontend)

**Use ES6+ Features:**
```javascript
// Good
const fetchData = async (url) => {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
    }
};

// Bad
function fetchData(url) {
    fetch(url).then(function(response) {
        return response.json();
    }).then(function(data) {
        // ...
    });
}
```

**Naming Conventions:**
```javascript
// camelCase for variables and functions
const myVariable = 'value';
function myFunction() {}

// PascalCase for classes
class MyClass {}

// UPPER_SNAKE_CASE for constants
const API_BASE_URL = 'http://localhost:8000';
```

---

## 🧪 Testing Guidelines

### Writing Tests

**Backend Tests:**
```python
# In tests/ directory
import pytest
from services.rule_engine import RuleEngine, DetectionData

def test_encroachment_detection():
    """Test encroachment violation detection"""
    engine = RuleEngine()
    data = DetectionData(
        plot_id="TEST_001",
        approved_area=10000.0,
        has_encroachment=True,
        encroachment_area=500.0
    )
    result = engine.evaluate(data)
    assert result.violation_type.value == "encroachment"
    assert result.severity.value == "medium"
```

**Frontend Tests:**
```javascript
// Manual testing checklist
// 1. Map loads correctly
// 2. Plots display with correct colors
// 3. Popups show correct information
// 4. API calls succeed
// 5. Error messages display properly
```

---

## 📁 Project Structure

```
Xcelerate/
├── backend/           # FastAPI backend
│   ├── main.py       # Main application
│   ├── services/     # Business logic
│   ├── models/       # ML models
│   ├── database/     # Database layer
│   └── utils/        # Utilities
├── frontend/         # Web dashboard
├── tests/            # Test files (create this)
├── docs/             # Additional documentation (create as needed)
└── deploy/           # Deployment scripts (create as needed)
```

---

## 🐛 Reporting Issues

### Bug Reports

Use this template:
```markdown
**Bug Description**
Clear description of the bug

**To Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen

**Screenshots**
If applicable

**Environment**
- OS: [e.g., Windows 11]
- Python Version: [e.g., 3.10]
- Browser: [e.g., Chrome 120]

**Additional Context**
Any other information
```

### Feature Requests

```markdown
**Problem Statement**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Mockups, examples, etc.
```

---

## 🚀 Development Workflow

### For New Features

1. **Planning Phase**
   - Discuss feature in GitHub Issues
   - Get approval from team lead
   - Break down into smaller tasks

2. **Development Phase**
   - Create feature branch
   - Implement incrementally
   - Write tests as you go
   - Update documentation

3. **Review Phase**
   - Self-review code
   - Run all tests
   - Create PR with detailed description
   - Address review comments

4. **Merge Phase**
   - Get approvals (minimum 1-2)
   - Squash commits if needed
   - Merge to develop branch

### For Bug Fixes

1. **Reproduce** - Confirm the bug exists
2. **Isolate** - Find root cause
3. **Fix** - Implement solution
4. **Test** - Verify fix works
5. **Document** - Update CHANGELOG.md

---

## 📚 Resources for Contributors

### Learning Resources

**FastAPI:**
- Official Docs: https://fastapi.tiangolo.com/
- Tutorial: https://fastapi.tiangolo.com/tutorial/

**PyTorch:**
- Official Docs: https://pytorch.org/docs/
- Tutorials: https://pytorch.org/tutorials/

**Google Earth Engine:**
- Python API: https://developers.google.com/earth-engine/guides/python_install
- Dataset Catalog: https://developers.google.com/earth-engine/datasets

**PostGIS:**
- Documentation: https://postgis.net/documentation/
- Spatial Queries: https://postgis.net/workshops/postgis-intro/

**Leaflet:**
- Documentation: https://leafletjs.com/reference.html
- Tutorials: https://leafletjs.com/examples.html

### Useful Commands

```bash
# Backend
cd backend
python main.py                    # Start API server
python -m pytest                  # Run tests
python models/unet.py             # Test ML model

# Frontend
cd frontend
python -m http.server 8080        # Start web server

# Git
git status                        # Check status
git log --oneline                 # View commits
git branch -a                     # List branches
git fetch origin                  # Update from remote

# Python
pip list                          # List installed packages
pip show package-name             # Package info
pip freeze > requirements.txt     # Export dependencies
```

---

## 🎯 Priority Areas for Contribution

### High Priority
1. **ML Model Training** - Train on real labeled data
2. **GEE Integration Testing** - Test with actual plots
3. **Database Population** - Import real plot boundaries
4. **Error Handling** - Improve error messages and handling
5. **Documentation** - Add code examples and tutorials

### Medium Priority
1. **Frontend Enhancements** - Better UI/UX
2. **Performance Optimization** - Speed up inference
3. **Batch Processing** - Handle multiple plots efficiently
4. **Monitoring** - Add Prometheus metrics
5. **Testing** - Increase test coverage

### Future Enhancements
1. **Drone Integration** - Add drone imagery support
2. **Mobile App** - Field inspector application
3. **Time Series Analysis** - Historical trend tracking
4. **Automated Reporting** - PDF report generation
5. **Multi-tenancy** - Support multiple organizations

---

## ✅ Code Review Checklist

### For Authors
- [ ] Code is self-documenting with clear names
- [ ] All functions have docstrings
- [ ] No commented-out code
- [ ] No print statements (use logger)
- [ ] Type hints added
- [ ] Tests pass
- [ ] Documentation updated

### For Reviewers
- [ ] Code follows project conventions
- [ ] Logic is clear and correct
- [ ] Edge cases handled
- [ ] No security vulnerabilities
- [ ] Performance considerations made
- [ ] Tests are adequate

---

## 📞 Communication

### GitHub Discussions
Use for:
- General questions
- Feature proposals
- Architecture discussions
- Best practices

### GitHub Issues
Use for:
- Bug reports
- Feature requests
- Task tracking

### Pull Request Comments
Use for:
- Code review feedback
- Implementation questions
- Specific line discussions

---

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in project documentation
- Acknowledged in presentations

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

## 🙏 Thank You!

Your contributions make this project better for everyone. Whether it's:
- Writing code
- Fixing bugs
- Improving documentation
- Suggesting features
- Reviewing PRs
- Testing and reporting issues

**Every contribution matters!**

---

**Questions?** Create a GitHub Discussion or reach out to the team lead.

**Happy Contributing! 🚀**
