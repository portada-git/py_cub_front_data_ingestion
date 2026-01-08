#!/bin/bash

# PortAda Backend Startup Script with UV

echo "Starting PortAda Backend API with UV..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "UV is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment and install dependencies
echo "Setting up environment with UV..."
uv sync

# Create data directory if it doesn't exist
mkdir -p /tmp/portada_data

# Start the server
echo "Starting FastAPI server..."
uv run python main.py