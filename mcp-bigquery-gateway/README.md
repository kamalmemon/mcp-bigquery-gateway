# MCP BigQuery Gateway

A Model Context Protocol (MCP) server for Google BigQuery integration with AI assistants.

**🐳 Docker Required**: This project is designed to run in Docker for simplicity and consistency.

## Features

- Execute SQL queries on BigQuery
- List datasets and tables
- Get table schemas
- Query validation
- Secure read-only access

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
- Google Cloud Project with BigQuery API enabled

## Quick Start

```bash
# 1. Clone and setup
git clone <repository-url>
cd mcp-bigquery-gateway

# 2. Authenticate with Google Cloud
make auth

# 3. Set your project
gcloud config set project YOUR_PROJECT_ID

# 4. Build (includes auth check and tests)
make build

# 5. Run
make run
```

## Usage

### Commands

- `make auth` - Setup Google Cloud authentication
- `make build` - Build Docker image (auto-checks auth and runs tests)
- `make run` - Start interactive Docker container
- `make test` - Run tests locally
- `make format` - Format and lint code
- `make clean` - Clean up

### Cursor Integration

Add this to your Cursor MCP settings:

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

**Remember to**:
- Replace `your-project-id` with your actual Google Cloud project ID
- Update the gcloud config path for your system
- Build the image first: `make build`

## Available Tools

- `execute_query` - Execute SQL queries
- `list_datasets` - List BigQuery datasets
- `list_tables` - List tables in a dataset
- `get_table_schema` - Get table schema
- `validate_query` - Validate SQL queries

## Authentication

The Docker container uses your local Google Cloud credentials:
- Run `make auth` to authenticate
- Your `~/.config/gcloud` directory is mounted read-only into the container
- Set your project with: `gcloud config set project YOUR_PROJECT_ID`

## License

MIT 