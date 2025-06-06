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
- [Google Cloud CLI (gcloud)](https://cloud.google.com/sdk/docs/install) installed
- **Cursor Pro** (for IDE integration)

## Quick Start

1. **Clone and install**:
```bash
git clone <repository-url>
cd <repository-name>
make install
```

2. **Authenticate with Google Cloud**:
```bash
make auth
```

3. **Set your Google Cloud project**:
```bash
gcloud config set project YOUR_PROJECT_ID
```

4. **Run the server**:
```bash
make run
```

## Detailed Installation

### 1. Install Dependencies

Install uv (if not already installed):
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

Install Google Cloud CLI:
```bash
# macOS
brew install google-cloud-sdk

# For other platforms, visit: https://cloud.google.com/sdk/docs/install
```

### 2. Clone and Setup

```bash
git clone <repository-url>
cd <repository-name>
make setup  # This will install dependencies and authenticate
```

### 3. Authentication

The `make auth` command will:
1. Authenticate you with Google Cloud (opens browser)
2. Set up Application Default Credentials for the BigQuery client
3. Guide you to set your default project

You can check your authentication status anytime:
```bash
make auth-check
```

## Configuration

### Environment Variables (Optional)

You can create a `.env` file for additional configuration:

```
PROJECT_ID=your-google-cloud-project-id
# GOOGLE_APPLICATION_CREDENTIALS is not needed when using Application Default Credentials
```

### Alternative: Service Account Authentication

If you prefer to use a service account JSON file instead of Application Default Credentials:

1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Set the environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

## Running the MCP Server

### Using Make (Recommended)

```bash
make run
```

### Manual Execution

```bash
# Direct Python execution
uv run python src/mcp_bigquery_server.py

# Using the installed script
uv run mcp-bigquery-server
```

The server will start and listen for MCP client connections via stdio (standard input/output).

## Connecting to Cursor

To integrate your MCP BigQuery Server with Cursor, you need to configure Cursor to recognize and use your server.

### Step 1: Locate Cursor Configuration

Find your Cursor configuration directory:

- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/cursor.mcp/`
- **Windows**: `%APPDATA%\Cursor\User\globalStorage\cursor.mcp\`
- **Linux**: `~/.config/Cursor/User/globalStorage/cursor.mcp/`

### Step 2: Create or Edit MCP Configuration

Create or edit the `settings.json` file in the configuration directory. You can use the provided example as a template:

```bash
# Copy the example configuration (macOS)
cp cursor_config_example.json ~/Library/Application\ Support/Cursor/User/globalStorage/cursor.mcp/settings.json

# For Windows
copy cursor_config_example.json %APPDATA%\Cursor\User\globalStorage\cursor.mcp\settings.json

# For Linux
cp cursor_config_example.json ~/.config/Cursor/User/globalStorage/cursor.mcp/settings.json
```

Or create the file manually with this content:

```json
{
  "mcpServers": {
    "bigquery": {
      "command": "uv",
      "args": [
        "run", 
        "python", 
        "/absolute/path/to/your/project/src/mcp_bigquery_server.py"
      ],
      "cwd": "/absolute/path/to/your/project"
    }
  }
}
```

**Important**: Replace `/absolute/path/to/your/project` with the actual absolute path to your project directory.

### Step 3: Alternative Configuration (Using Virtual Environment)

If you prefer to use the virtual environment directly:

```json
{
  "mcpServers": {
    "bigquery": {
      "command": "/absolute/path/to/your/project/.venv/bin/python",
      "args": [
        "/absolute/path/to/your/project/src/mcp_bigquery_server.py"
      ],
      "cwd": "/absolute/path/to/your/project"
    }
  }
}
```

### Step 4: Restart Cursor

After saving the configuration:

1. **Close Cursor completely**
2. **Restart Cursor**
3. **Open your project**

### Step 5: Verify Connection

To verify that your MCP server is connected:

1. Open Cursor
2. Look for MCP server indicators in the status bar or settings
3. Try using the BigQuery tools in a chat or code context

### Step 6: Test the Integration

Once connected, you can test the integration by asking Cursor to:

```
Can you list the datasets in my BigQuery project?
```

or

```
Execute this query: SELECT * FROM `your-project.your-dataset.your-table` LIMIT 10
```

## Available Make Commands

Run `make` or `make help` to see all available commands:

- `make setup` - Complete setup (install + auth)
- `make auth` - Authenticate with Google Cloud
- `make auth-check` - Check authentication status
- `make run` - Run the MCP server
- `make test` - Run tests
- `make lint` - Run linting checks
- `make format` - Format code
- `make clean` - Clean up cache files
- `make info` - Show project information

## Troubleshooting

### Common Issues

1. **Authentication errors**: 
   - Run `make auth-check` to verify your authentication status
   - Run `make auth` to re-authenticate if needed
   - Ensure your Google Cloud project has BigQuery API enabled

2. **Server not starting**: 
   - Check that all dependencies are installed: `make install`
   - Verify Python version: `python --version` (should be 3.10+)
   - Check authentication: `make auth-check`

3. **Cursor not recognizing the server**:
   - Ensure the path in the configuration is absolute, not relative
   - Verify the configuration file is in the correct location
   - Restart Cursor completely after configuration changes

4. **Permission errors**:
   - Make sure the Python script is executable
   - Check that the virtual environment has proper permissions

### Debugging

To debug connection issues:

1. **Test the server manually**:
   ```bash
   make run
   ```

2. **Check authentication**:
   ```bash
   make auth-check
   ```

3. **Check Cursor logs**:
   - Open Cursor Developer Tools (Help → Toggle Developer Tools)
   - Look for MCP-related error messages in the console

4. **Verify configuration**:
   - Double-check JSON syntax in configuration files
   - Ensure all paths are correct and absolute

## Available Tools

Once connected, your MCP server provides these tools:

- **execute_query**: Execute SQL queries against BigQuery
- **list_datasets**: List all datasets in a BigQuery project
- **list_tables**: List all tables in a specific dataset
- **get_table_schema**: Get the schema of a specific table
- **validate_query**: Validate SQL queries without executing them

## Development

### Setup Development Environment

Install development dependencies:

```bash
make dev
```

### Project Structure

```
├── src/
│   ├── mcp_bigquery_server.py    # Main MCP server implementation
│   ├── bigquery_client.py        # BigQuery client wrapper
│   └── utils.py                  # Utility functions
├── tests/                        # Test files
├── Makefile                      # Build and setup commands
├── pyproject.toml                # Project configuration and dependencies
├── cursor_config_example.json    # Example Cursor configuration
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

### Running Tests

```bash
make test
```

### Code Formatting and Linting

```bash
make format  # Format code
make lint    # Check linting
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

## References

This implementation follows the Model Context Protocol (MCP) specification and is inspired by the comprehensive tutorial available at [DigitalOcean's MCP Server in Python guide](https://www.digitalocean.com/community/tutorials/mcp-server-python).

## License

MIT License 