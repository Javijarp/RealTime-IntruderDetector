#!/bin/bash

# Face Recognition System - Docker Deployment Script
# This script helps with common Docker operations for the Face Recognition System

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function for colored output
print_status() {
    echo -e "${GREEN}[*]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if docker-compose.yml exists
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "docker-compose.yml not found in $SCRIPT_DIR"
    exit 1
fi

# Navigation to script directory
cd "$SCRIPT_DIR"

# Commands
case "${1:-help}" in
    start|up)
        print_status "Starting Face Recognition System containers..."
        docker-compose up -d --build
        print_status "Waiting for services to be healthy..."
        sleep 5
        docker-compose ps
        echo ""
        print_status "✓ Services started successfully!"
        echo ""
        print_status "Access the system:"
        echo "  • Frontend:  http://192.168.5.74:3000"
        echo "  • Backend:   http://192.168.5.74:8080/api"
        echo "  • Database:  192.168.5.74:5432"
        ;;
    
    stop|down)
        print_status "Stopping all containers..."
        docker-compose down
        print_status "✓ All containers stopped"
        ;;
    
    restart)
        print_status "Restarting all services..."
        docker-compose restart
        print_status "✓ Services restarted"
        ;;
    
    rebuild)
        print_status "Rebuilding and restarting all services..."
        docker-compose up -d --build
        print_status "✓ Services rebuilt and restarted"
        ;;
    
    logs)
        if [ -n "$2" ]; then
            print_status "Showing logs for $2..."
            docker-compose logs -f "$2"
        else
            print_status "Showing logs for all services..."
            docker-compose logs -f
        fi
        ;;
    
    ps|status)
        print_status "Container status:"
        docker-compose ps
        ;;
    
    clean)
        print_warning "This will stop and remove all containers and volumes (database data will be lost)!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Cleaning up..."
            docker-compose down -v
            print_status "✓ All containers and volumes removed"
        else
            print_status "Clean cancelled"
        fi
        ;;
    
    shell)
        if [ -z "$2" ]; then
            print_error "Usage: $0 shell <service>"
            echo "  Available services: backend, frontend, db"
            exit 1
        fi
        print_status "Entering shell for $2..."
        docker-compose exec "$2" /bin/sh
        ;;
    
    build)
        print_status "Building images..."
        docker-compose build
        print_status "✓ Build complete"
        ;;
    
    help|--help|-h)
        echo "Face Recognition System - Docker Control Script"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start|up              Start all services (build if needed)"
        echo "  stop|down             Stop all services"
        echo "  restart               Restart all services"
        echo "  rebuild               Rebuild images and restart"
        echo "  logs [service]        View logs (all or specific service)"
        echo "  ps|status             Show container status"
        echo "  shell <service>       Open shell in a service"
        echo "  build                 Build images without starting"
        echo "  clean                 Remove all containers and volumes (⚠️ deletes database!)"
        echo "  help                  Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 start              # Start everything"
        echo "  $0 logs backend       # View backend logs"
        echo "  $0 shell db          # Access PostgreSQL shell"
        echo ""
        echo "Access URLs:"
        echo "  Frontend:  http://192.168.5.74:3000"
        echo "  Backend:   http://192.168.5.74:8080/api"
        echo ""
        ;;
    
    *)
        print_error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
