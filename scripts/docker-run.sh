#!/bin/bash

# MCP BigQuery Gateway Docker Runner
# This script builds and runs the MCP server in Docker

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
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the Docker image
print_status "Building MCP BigQuery Gateway Docker image..."
docker build -t mcp-bigquery-gateway .

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    print_warning "PROJECT_ID environment variable is not set."
    print_warning "You can set it by running: export PROJECT_ID=your-project-id"
    print_warning "Or pass it when running: PROJECT_ID=your-project-id $0"
fi

# Run the container
print_status "Starting MCP BigQuery Gateway server..."
print_status "The server will run in interactive mode and communicate via stdin/stdout"
print_status "Press Ctrl+C to stop the server"

# Run with environment variables and proper interactive flags
docker run -i \
    --rm \
    --name mcp-bigquery-gateway \
    -e PROJECT_ID="${PROJECT_ID:-}" \
    -e GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-}" \
    -e LOG_LEVEL="${LOG_LEVEL:-WARNING}" \
    -e DEFAULT_DATASET="${DEFAULT_DATASET:-}" \
    -e QUERY_TIMEOUT="${QUERY_TIMEOUT:-300}" \
    -e MAX_RESULTS="${MAX_RESULTS:-10000}" \
    -v "${HOME}/.config/gcloud:/home/app/.config/gcloud:ro" \
    mcp-bigquery-gateway 