# Python Version Compatibility

## Recommended Python Versions

This project has been tested with:
- **Python 3.11** (Recommended)
- **Python 3.12** (Recommended)
- **Python 3.13** (Should work)
- **Python 3.14** (May have compatibility issues with some packages)

## If you encounter pandas installation errors with Python 3.14:

### Option 1: Use Python 3.11 or 3.12 (Recommended)
```bash
# Using pyenv (if installed)
pyenv install 3.12.0
pyenv local 3.12.0

# Or create a virtual environment with a specific Python version
python3.12 -m venv venv
source venv/bin/activate
```

### Option 2: Install pandas from source or use pre-built wheels
```bash
pip install --upgrade pip
pip install pandas --no-cache-dir
```

### Option 3: Use a Docker container with Python 3.12
The Dockerfile uses Python 3.11, which is compatible with all dependencies.

## Checking your Python version
```bash
python3 --version
# or
python --version
```

