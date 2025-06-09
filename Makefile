# MCP BigQuery Gateway - Docker-First Makefile

.PHONY: help auth build run test format clean

help:
	@echo "MCP BigQuery Gateway (Docker-First)"
	@echo ""
	@echo "Commands:"
	@echo "  auth   - Setup Google Cloud authentication"
	@echo "  build  - Build Docker image (includes auth check and tests)"
	@echo "  run    - Run interactive Docker container"
	@echo "  test   - Run tests locally"
	@echo "  format - Format and lint code"
	@echo "  clean  - Clean up"

auth:
	@echo "🔐 Setting up Google Cloud authentication..."
	@which gcloud > /dev/null || (echo "❌ Error: gcloud CLI not installed. Install from: https://cloud.google.com/sdk/docs/install" && exit 1)
	@echo "Opening browser for Google Cloud authentication..."
	gcloud auth login
	gcloud auth application-default login
	@echo "✅ Authentication complete!"
	@echo "💡 Remember to set your project: gcloud config set project YOUR_PROJECT_ID"

build:
	@echo "🏗️  Building MCP BigQuery Gateway..."
	@echo ""
	@echo "📋 Step 1: Checking Google Cloud authentication..."
	@gcloud auth application-default print-access-token > /dev/null 2>&1 || \
		(echo "❌ Not authenticated. Running 'make auth'..." && make auth)
	@echo "✅ Authentication verified"
	@echo ""
	@echo "🧪 Step 2: Running tests..."
	@make test
	@echo ""
	@echo "🐳 Step 3: Building Docker image..."
	docker build -t mcp-bigquery-gateway .
	@echo ""
	@echo "✅ Build complete!"
	@echo ""
	@echo "📋 Cursor MCP Configuration:"
	@echo "Copy this to your Cursor MCP settings (.cursor/mcp.json):"
	@echo ""
	@PROJECT_ID=$$(gcloud config get-value project 2>/dev/null) && \
	GCLOUD_PATH="$$HOME/.config/gcloud" && \
	echo "{" && \
	echo "  \"mcpServers\": {" && \
	echo "    \"mcp-bigquery-gateway\": {" && \
	echo "      \"command\": \"docker\"," && \
	echo "      \"args\": [" && \
	echo "        \"run\", \"-i\", \"--rm\"," && \
	echo "        \"-e\", \"PROJECT_ID=$$PROJECT_ID\"," && \
	echo "        \"-v\", \"$$GCLOUD_PATH:/home/app/.config/gcloud:ro\"," && \
	echo "        \"mcp-bigquery-gateway\"" && \
	echo "      ]" && \
	echo "    }" && \
	echo "  }" && \
	echo "}"
	@echo ""
	@echo "💡 Save this to: ~/.cursor/mcp.json (global) or ./.cursor/mcp.json (project-specific)"
	@echo "💡 Then restart Cursor"

run:
	@echo "🚀 Starting MCP BigQuery Gateway in Docker..."
	@PROJECT_ID=$$(gcloud config get-value project 2>/dev/null) && \
	if [ -z "$$PROJECT_ID" ] || [ "$$PROJECT_ID" = "(unset)" ]; then \
		echo "❌ No Google Cloud project set. Please run:"; \
		echo "   gcloud config set project YOUR_PROJECT_ID"; \
		exit 1; \
	fi && \
	echo "📊 Using project: $$PROJECT_ID" && \
	docker run -it --rm \
		-e PROJECT_ID=$$PROJECT_ID \
		-v "$$HOME/.config/gcloud:/home/app/.config/gcloud:ro" \
		mcp-bigquery-gateway

test:
	@echo "🧪 Running tests..."
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		uv sync; \
	fi
	uv run pytest tests/ -v

format:
	@echo "🎨 Formatting and linting code..."
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		uv sync; \
	fi
	uv run black src/ tests/
	uv run ruff check --fix src/ tests/
	@echo "✅ Code formatted and linted"

clean:
	@echo "🧹 Cleaning up..."
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	docker system prune -f 2>/dev/null || true
	@echo "✅ Cleanup complete" 