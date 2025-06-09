# MCP BigQuery Gateway

A [Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) server for Google BigQuery integration with AI assistants.

⚠️ Disclaimer: This code is largely generated through AI-assisted development ("vibe coding"). While it has been tested, we make no guarantees about correctness, security, or reliability. Use at your own risk in production environments.

## Prerequisites

**Required**
- [🐳 Docker](https://docs.docker.com/get-docker/) 
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
- Google Cloud Project with BigQuery API enabled

## Features

- List datasets and tables  
- Get table schemas
- Execute SQL queries 
    - With **🔒 read-only access** - Only `SELECT` queries and `WITH` clauses (Common Table Expressions) are allowed. All DDL (CREATE, DROP, ALTER), DML (INSERT, UPDATE, DELETE), and other write operations are blocked for security.
- Query validation

### Available Tools

Once configured, these tools will be available:

- `execute_query` - Execute SQL queries
- `list_datasets` - List BigQuery datasets  
- `list_tables` - List tables in a dataset
- `get_table_schema` - Get table schema
- `validate_query` - Validate SQL queries


## Setup

### 1. Clone and Authenticate

```bash
# Clone the repository
git clone <repository-url>
cd mcp-bigquery-gateway

# Authenticate with Google Cloud
make auth

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Build Docker Container

```bash
# Build the Docker image and generate Cursor configuration
make build
```

The `make build` command will:
- ✅ Verify Google Cloud authentication
- 🧪 Run all tests
- 🐳 Build the Docker container locally
- 📋 Generate the Cursor MCP configuration JSON

### 3. Configure Cursor

After `make build` completes, it will display a JSON configuration. Copy this JSON and save it to either:

- **Global configuration**: `~/.cursor/mcp.json` (applies to all projects)
- **Project-specific**: `./.cursor/mcp.json` (applies only to this project)

> 💡 **Tip**: You can also find an example configuration in [examples/cursor_config_example.json](examples/cursor_config_example.json)

Then restart Cursor.

### 4. Test the Setup

```bash
# Test the container runs correctly
make run

# You should see the MCP server start and wait for connections
```

## Usage

### Commands

- `make auth` - Setup Google Cloud authentication
- `make build` - Build Docker image and show Cursor config
- `make run` - Start interactive Docker container  
- `make test` - Run tests locally
- `make format` - Format and lint code
- `make clean` - Clean up

## Authentication

The Docker container uses your local Google Cloud credentials:
- Run `make auth` to authenticate with Google Cloud
- Your `~/.config/gcloud` directory is mounted read-only into the container
- The configuration automatically uses your current project from `gcloud config get-value project`

## Troubleshooting

- **"No project set"**: Run `gcloud config set project YOUR_PROJECT_ID`
- **"Not authenticated"**: Run `make auth` 
- **"Docker image not found"**: Run `make build` first
- **Cursor not connecting**: Ensure you saved the JSON to the correct `.cursor/mcp.json` file and restarted Cursor

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 