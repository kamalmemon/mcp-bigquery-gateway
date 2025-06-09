#!/usr/bin/env python3
"""
MCP BigQuery Server

A Model Context Protocol server that provides BigQuery integration capabilities.
"""

import asyncio
import json
import logging
import os

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from bigquery_client import BigQueryClient
from utils import setup_logging, validate_sql_query

# Configure logging
logger = logging.getLogger(__name__)

# Global BigQuery client
bigquery_client: BigQueryClient | None = None


def get_project_id() -> str | None:
    """Get project ID from environment or gcloud config."""
    # First try environment variable
    project_id = os.getenv("PROJECT_ID")
    if project_id:
        logger.info(f"Using project ID from environment: {project_id}")
        return project_id

    # Try to get from gcloud config
    try:
        import subprocess

        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"], capture_output=True, text=True, check=True
        )
        project_id = result.stdout.strip()
        if project_id and project_id != "(unset)":
            logger.info(f"Using project ID from gcloud config: {project_id}")
            return project_id
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Could not get project ID from gcloud config")

    logger.warning(
        "No project ID found. Please set PROJECT_ID environment variable "
        "or run 'gcloud config set project YOUR_PROJECT_ID'"
    )
    return None


def get_bigquery_client() -> BigQueryClient:
    """Get or create BigQuery client."""
    global bigquery_client
    if bigquery_client is None:
        project_id = get_project_id()
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        bigquery_client = BigQueryClient(project_id=project_id, credentials_path=credentials_path)
    return bigquery_client


# Create the server instance
server = Server("mcp-bigquery-gateway")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="execute_query",
            description="Execute a SQL query against BigQuery and return results",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"},
                    "project_id": {
                        "type": "string",
                        "description": "Google Cloud project ID (optional)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 1000,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="list_datasets",
            description="List all datasets in a BigQuery project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Google Cloud project ID (optional)",
                    }
                },
            },
        ),
        types.Tool(
            name="list_tables",
            description="List all tables in a BigQuery dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "string",
                        "description": "Dataset ID to list tables from",
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Google Cloud project ID (optional)",
                    },
                },
                "required": ["dataset_id"],
            },
        ),
        types.Tool(
            name="get_table_schema",
            description="Get the schema of a BigQuery table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_id": {
                        "type": "string",
                        "description": "Table ID in format 'dataset.table'",
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Google Cloud project ID (optional)",
                    },
                },
                "required": ["table_id"],
            },
        ),
        types.Tool(
            name="validate_query",
            description="Validate a SQL query without executing it",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "SQL query to validate"}},
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Handle tool calls."""
    if arguments is None:
        arguments = {}

    try:
        if name == "execute_query":
            query = arguments.get("query")
            if not query:
                return [types.TextContent(type="text", text="Error: query parameter is required")]

            # Validate query
            if not validate_sql_query(query):
                return [
                    types.TextContent(
                        type="text", text="Error: Invalid or potentially unsafe SQL query"
                    )
                ]

            client = get_bigquery_client()
            project_id = arguments.get("project_id")
            max_results = arguments.get("max_results", 1000)

            results = await client.execute_query(
                query, project_id=project_id, max_results=max_results
            )

            return [
                types.TextContent(
                    type="text",
                    text=f"Query Results:\n{json.dumps(results, indent=2, default=str)}",
                )
            ]

        elif name == "list_datasets":
            client = get_bigquery_client()
            project_id = arguments.get("project_id")

            datasets = await client.list_datasets(project_id=project_id)

            return [
                types.TextContent(type="text", text=f"Datasets:\n{json.dumps(datasets, indent=2)}")
            ]

        elif name == "list_tables":
            dataset_id = arguments.get("dataset_id")
            if not dataset_id:
                return [
                    types.TextContent(type="text", text="Error: dataset_id parameter is required")
                ]

            client = get_bigquery_client()
            project_id = arguments.get("project_id")

            tables = await client.list_tables(dataset_id=dataset_id, project_id=project_id)

            return [
                types.TextContent(
                    type="text", text=f"Tables in {dataset_id}:\n{json.dumps(tables, indent=2)}"
                )
            ]

        elif name == "get_table_schema":
            table_id = arguments.get("table_id")
            if not table_id:
                return [
                    types.TextContent(type="text", text="Error: table_id parameter is required")
                ]

            client = get_bigquery_client()
            project_id = arguments.get("project_id")

            schema = await client.get_table_schema(table_id=table_id, project_id=project_id)

            return [
                types.TextContent(
                    type="text", text=f"Schema for {table_id}:\n{json.dumps(schema, indent=2)}"
                )
            ]

        elif name == "validate_query":
            query = arguments.get("query")
            if not query:
                return [types.TextContent(type="text", text="Error: query parameter is required")]

            # Basic validation
            is_valid = validate_sql_query(query)
            if not is_valid:
                return [
                    types.TextContent(
                        type="text", text="Query validation failed: Invalid or unsafe query"
                    )
                ]

            # BigQuery dry run validation
            client = get_bigquery_client()
            validation_result = await client.validate_query(query)

            return [
                types.TextContent(
                    type="text", text=f"Query validation: {json.dumps(validation_result, indent=2)}"
                )
            ]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point."""
    # Use environment variable for log level, default to WARNING for MCP Inspector
    log_level = os.getenv("LOG_LEVEL", "WARNING")
    setup_logging(log_level)
    logger.info("Starting MCP BigQuery Server...")

    try:
        # Initialize BigQuery client
        get_bigquery_client()
        logger.info("BigQuery client initialized successfully")

        # Run the server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Server running with stdio transport")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-bigquery-gateway",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
