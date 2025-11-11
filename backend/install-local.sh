#!/bin/bash
# Install dependencies locally with Python version check

echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)

if [ "$python_version" != "3.11" ] && [ "$python_version" != "3.12" ] && [ "$python_version" != "3.13" ]; then
    echo "Warning: You're using Python $python_version"
    echo "This project is designed for Python 3.11-3.13 (Docker uses 3.11)"
    echo ""
    echo "For Python 3.14+, setting PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1"
    export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
fi

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Done!"

