#!/bin/bash

# Database Service Docker Build Script

set -e

echo "🐳 Building Database Service Docker Image..."

# Build the Docker image
docker build -t database-service:latest .

echo "✅ Docker image built successfully!"

echo "🚀 Starting Database Service with Docker Compose..."

# Start the service
docker-compose up -d

echo "✅ Database Service is starting up!"
echo "📊 Service will be available at: http://localhost:8000"
echo "🔍 Health check endpoint: http://localhost:8000/health"
echo "📝 API documentation: http://localhost:8000/docs"

echo ""
echo "📋 Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop service: docker-compose down"
echo "  - Restart service: docker-compose restart"
echo "  - Rebuild and restart: docker-compose up -d --build" 