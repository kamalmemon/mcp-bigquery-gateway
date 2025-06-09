# Docker Setup for MCP BigQuery Gateway

This document explains how to run the MCP BigQuery Gateway server using Docker.

## Quick Start

1. **Build and run with the provided script**:
```bash
./docker-run.sh
```

2. **Or manually with Docker**:
```bash
# Build the image
docker build -t mcp-bigquery-gateway .

# Run the server
docker run -i --rm \
  -e PROJECT_ID=your-project-id \
  -v "${HOME}/.config/gcloud:/home/app/.config/gcloud:ro" \
  mcp-bigquery-gateway
```

## Authentication

The Docker container supports two authentication methods:

### 1. Application Default Credentials (Recommended)
Mount your gcloud configuration directory:
```bash
-v "${HOME}/.config/gcloud:/home/app/.config/gcloud:ro"
```

Make sure you've authenticated locally first:
```bash
gcloud auth application-default login
```

### 2. Service Account Key File
Mount your service account JSON file:
```bash
-v "/path/to/your/service-account-key.json:/app/credentials/key.json:ro" \
-e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/key.json
```

## Environment Variables

- `PROJECT_ID`: Your Google Cloud project ID (required)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key (optional)
- `LOG_LEVEL`: Logging level (default: WARNING)
- `DEFAULT_DATASET`: Default BigQuery dataset (optional)
- `QUERY_TIMEOUT`: Query timeout in seconds (default: 300)
- `MAX_RESULTS`: Maximum results per query (default: 10000)

## Using with Cursor

Update your Cursor MCP configuration to use the Docker command:

```json
{
  "mcpServers": {
    "bigquery": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "PROJECT_ID=your-project-id",
        "-v", "/Users/yourusername/.config/gcloud:/home/app/.config/gcloud:ro",
        "mcp-bigquery-gateway"
      ]
    }
  }
}
```

Make sure to:
1. Replace `your-project-id` with your actual Google Cloud project ID
2. Update the gcloud config path if different on your system
3. Build the Docker image first: `docker build -t mcp-bigquery-gateway .`

## Building the Image

The Dockerfile uses multi-stage building with:
- Python 3.11 slim base image
- UV for fast dependency management
- Non-root user for security
- Only necessary files copied (see `.dockerignore`)

Build manually:
```bash
docker build -t mcp-bigquery-gateway .
```

## Troubleshooting

1. **Permission errors**: Make sure your mounted gcloud directory is readable
2. **Authentication issues**: Verify your local gcloud authentication works first
3. **Project not found**: Ensure PROJECT_ID environment variable is set correctly 