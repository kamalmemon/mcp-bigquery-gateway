# MCP BigQuery Server

A Model Context Protocol (MCP) server that provides seamless integration with Google BigQuery, enabling AI assistants to query and analyze data directly from BigQuery datasets.

## Features

- Connect to BigQuery datasets
- Execute SQL queries
- Retrieve table schemas and metadata
- Handle authentication with Google Cloud
- Secure query execution with proper error handling

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (for dependency management)
- Google Cloud Project with BigQuery API enabled
- Service account credentials or user authentication

## Installation

1. Install uv (if not already installed):
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

2. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

3. Install dependencies with uv:
```bash
uv sync
```

4. Set up Google Cloud authentication:
   - Create a service account in your Google Cloud Console
   - Download the service account key JSON file
   - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your key file

## Configuration

Create a `.env` file in the root directory with your configuration:

```
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
PROJECT_ID=your-google-cloud-project-id
```

## Usage

Start the MCP server:

```bash
uv run python src/mcp_bigquery_server.py
```

Or use the installed script:

```bash
uv run mcp-bigquery-server
```

The server will be available for MCP clients to connect and execute BigQuery operations.

## Development

### Setup Development Environment

Install development dependencies:

```bash
uv sync --extra dev
```

### Project Structure

```
├── src/
│   ├── mcp_bigquery_server.py    # Main MCP server implementation
│   ├── bigquery_client.py        # BigQuery client wrapper
│   └── utils.py                  # Utility functions
├── tests/                        # Test files
├── pyproject.toml                # Project configuration and dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

### Running Tests

```bash
uv run pytest
```

### Code Formatting and Linting

Format code with Black:
```bash
uv run black src/ tests/
```

Lint with Ruff:
```bash
uv run ruff check src/ tests/
```

Type checking with mypy:
```bash
uv run mypy src/
```

### Adding Dependencies

Add a new dependency:
```bash
uv add package-name
```

Add a development dependency:
```bash
uv add --dev package-name
```

## License

MIT License 