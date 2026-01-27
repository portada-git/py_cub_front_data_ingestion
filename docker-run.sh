#!/bin/bash

# PortAda Docker Compose Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker and Docker Compose are installed
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev     Start development environment"
    echo "  prod    Start production environment"
    echo "  stop    Stop all services"
    echo "  logs    Show logs"
    echo "  clean   Clean up containers and volumes"
    echo "  build   Build all images"
    echo "  help    Show this help message"
}

# Start development environment
start_dev() {
    print_status "Starting PortAda development environment..."
    docker-compose -f docker-compose.dev.yml up --build -d
    print_status "Development environment started!"
    print_status "Frontend: http://localhost:5173"
    print_status "Backend API: http://localhost:8000"
    print_status "API Docs: http://localhost:8000/api/docs"
}

# Start production environment
start_prod() {
    print_status "Starting PortAda production environment..."
    docker-compose up --build -d
    print_status "Production environment started!"
    print_status "Frontend: http://localhost:5173"
    print_status "Backend API: http://localhost:8000"
}

# Stop all services
stop_services() {
    print_status "Stopping all PortAda services..."
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    docker-compose down 2>/dev/null || true
    print_status "All services stopped."
}

# Show logs
show_logs() {
    print_status "Showing logs for all services..."
    docker-compose -f docker-compose.dev.yml logs -f 2>/dev/null || docker-compose logs -f
}

# Clean up
clean_up() {
    print_warning "This will remove all containers, images, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up PortAda containers and volumes..."
        stop_services
        docker-compose -f docker-compose.dev.yml down -v --rmi all 2>/dev/null || true
        docker-compose down -v --rmi all 2>/dev/null || true
        print_status "Cleanup completed."
    else
        print_status "Cleanup cancelled."
    fi
}

# Build images
build_images() {
    print_status "Building all Docker images..."
    docker-compose -f docker-compose.dev.yml build
    print_status "All images built successfully."
}

# Main script logic
main() {
    check_dependencies

    case "${1:-help}" in
        "dev")
            start_dev
            ;;
        "prod")
            start_prod
            ;;
        "stop")
            stop_services
            ;;
        "logs")
            show_logs
            ;;
        "clean")
            clean_up
            ;;
        "build")
            build_images
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

main "$@"