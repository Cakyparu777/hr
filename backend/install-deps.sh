#!/bin/bash
# Install dependencies script for development
# This is useful when using volume mounts in Docker

echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "Dependencies installed successfully!"

