#!/bin/bash

# PortAda Backend Startup Script with UV

echo "Starting PortAda Backend API with UV..."

# Set JAVA_HOME if not already set
if [ -z "$JAVA_HOME" ]; then
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
    echo "JAVA_HOME set to: $JAVA_HOME"
fi

# Check if Java is available
if ! command -v java &> /dev/null; then
    echo "Java is not installed or not in PATH. Please install Java 17 or later."
    exit 1
fi

echo "Java version:"
java -version

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