# MCP BigQuery Server

A Model Context Protocol (MCP) server that provides seamless integration with Google BigQuery, enabling AI assistants to query and analyze data directly from BigQuery datasets.

## Features

- Connect to BigQuery datasets
- Execute SQL queries
- Retrieve table schemas and metadata
- Handle authentication with Google Cloud
- Secure query execution with proper error handling

## Prerequisites

- Python 3.8+
- Google Cloud Project with BigQuery API enabled
- Service account credentials or user authentication

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Cloud authentication:
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
python src/mcp_bigquery_server.py
```

The server will be available for MCP clients to connect and execute BigQuery operations.

## Development

### Project Structure

```
├── src/
│   ├── mcp_bigquery_server.py    # Main MCP server implementation
│   ├── bigquery_client.py        # BigQuery client wrapper
│   └── utils.py                  # Utility functions
├── tests/                        # Test files
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

### Running Tests

```bash
python -m pytest tests/
```

## License

MIT License 