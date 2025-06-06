# MCP BigQuery Server Makefile
# Provides convenient commands for setup, authentication, and development

.PHONY: help install auth auth-check setup dev test lint format clean run

# Default target
help:
	@echo "MCP BigQuery Server - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install     - Install dependencies with uv"
	@echo "  make setup       - Complete setup (install + auth)"
	@echo ""
	@echo "Authentication Commands:"
	@echo "  make auth        - Authenticate with Google Cloud (interactive)"
	@echo "  make auth-check  - Check current authentication status"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev         - Install development dependencies"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting checks"
	@echo "  make format      - Format code with black and ruff"
	@echo ""
	@echo "Server Commands:"
	@echo "  make run         - Run the MCP server"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean       - Clean up cache and temporary files"

# Install dependencies
install:
	@echo "Installing dependencies with uv..."
	uv sync

# Install development dependencies
dev:
	@echo "Installing development dependencies..."
	uv sync --extra dev

# Check if gcloud is installed
check-gcloud:
	@which gcloud > /dev/null || (echo "Error: gcloud CLI is not installed. Please install it first:" && \
		echo "  macOS: brew install google-cloud-sdk" && \
		echo "  Linux: https://cloud.google.com/sdk/docs/install" && \
		echo "  Windows: https://cloud.google.com/sdk/docs/install" && \
		exit 1)

# Authenticate with Google Cloud
auth: check-gcloud
	@echo "Authenticating with Google Cloud..."
	@echo "This will open a browser window for authentication."
	gcloud auth login
	@echo ""
	@echo "Setting up Application Default Credentials..."
	gcloud auth application-default login
	@echo ""
	@echo "✅ Authentication complete!"
	@echo ""
	@echo "Optional: Set your default project with:"
	@echo "  gcloud config set project YOUR_PROJECT_ID"

# Check authentication status
auth-check: check-gcloud
	@echo "Checking Google Cloud authentication status..."
	@echo ""
	@echo "Current authenticated account:"
	@gcloud auth list --filter=status:ACTIVE --format="table(account,status)" || echo "No active authentication found"
	@echo ""
	@echo "Application Default Credentials:"
	@gcloud auth application-default print-access-token > /dev/null 2>&1 && \
		echo "✅ Application Default Credentials are configured" || \
		echo "❌ Application Default Credentials not found. Run 'make auth' to set up."
	@echo ""
	@echo "Current project:"
	@gcloud config get-value project 2>/dev/null || echo "No default project set"

# Complete setup
setup: install auth
	@echo ""
	@echo "🎉 Setup complete! Your MCP BigQuery Server is ready to use."
	@echo ""
	@echo "Next steps:"
	@echo "1. Set your default project: gcloud config set project YOUR_PROJECT_ID"
	@echo "2. Configure Cursor with the provided example config"
	@echo "3. Run the server: make run"

# Run tests
test:
	@echo "Running tests..."
	uv run pytest

# Run linting
lint:
	@echo "Running linting checks..."
	uv run ruff check src/ tests/

# Format code
format:
	@echo "Formatting code..."
	uv run black src/ tests/
	uv run ruff check --fix src/ tests/

# Run the MCP server
run:
	@echo "Starting MCP BigQuery Server..."
	@echo "Press Ctrl+C to stop the server"
	uv run python src/mcp_bigquery_server.py

# Clean up
clean:
	@echo "Cleaning up cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Show project info
info: check-gcloud
	@echo "MCP BigQuery Server Project Information:"
	@echo ""
	@echo "Current Google Cloud Project:"
	@gcloud config get-value project 2>/dev/null || echo "No default project set"
	@echo ""
	@echo "Available BigQuery datasets (if authenticated):"
	@bq ls 2>/dev/null || echo "Unable to list datasets. Check authentication and project setup." 