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
- **Cursor Pro** (for IDE integration)

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

## Running the MCP Server

### Method 1: Direct Python Execution

Start the MCP server directly:

```bash
uv run python src/mcp_bigquery_server.py
```

### Method 2: Using the Installed Script

```bash
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

## Troubleshooting

### Common Issues

1. **Server not starting**: 
   - Check that all dependencies are installed: `uv sync`
   - Verify Python version: `python --version` (should be 3.10+)
   - Check Google Cloud credentials are properly configured

2. **Cursor not recognizing the server**:
   - Ensure the path in the configuration is absolute, not relative
   - Verify the configuration file is in the correct location
   - Restart Cursor completely after configuration changes

3. **Permission errors**:
   - Make sure the Python script is executable
   - Check that the virtual environment has proper permissions

4. **BigQuery authentication errors**:
   - Verify your service account key file exists and is readable
   - Check that the `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set correctly
   - Ensure your service account has BigQuery permissions

### Debugging

To debug connection issues:

1. **Test the server manually**:
   ```bash
   uv run python src/mcp_bigquery_server.py
   ```

2. **Check Cursor logs**:
   - Open Cursor Developer Tools (Help → Toggle Developer Tools)
   - Look for MCP-related error messages in the console

3. **Verify configuration**:
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
├── cursor_config_example.json    # Example Cursor configuration
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

## References

This implementation follows the Model Context Protocol (MCP) specification and is inspired by the comprehensive tutorial available at [DigitalOcean's MCP Server in Python guide](https://www.digitalocean.com/community/tutorials/mcp-server-python).

## License

MIT License 