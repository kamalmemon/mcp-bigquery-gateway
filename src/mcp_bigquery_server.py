#!/usr/bin/env python3
"""
MCP BigQuery Server

A Model Context Protocol server that provides BigQuery integration capabilities.
"""

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)

from bigquery_client import BigQueryClient
from utils import setup_logging, validate_sql_query

# Configure logging
logger = logging.getLogger(__name__)


class MCPBigQueryServer:
    """MCP Server for BigQuery operations."""

    def __init__(self):
        self.server = Server("mcp-bigquery-server")
        self.bigquery_client = None
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available BigQuery tools."""
            return [
                Tool(
                    name="execute_query",
                    description="Execute a SQL query against BigQuery and return results",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "SQL query to execute"},
                            "project_id": {
                                "type": "string",
                                "description": "Google Cloud project ID (optional, uses default)",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 1000)",
                                "default": 1000,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="list_datasets",
                    description="List all datasets in a BigQuery project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "Google Cloud project ID (optional, uses default)",
                            }
                        },
                    },
                ),
                Tool(
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
                                "description": "Google Cloud project ID (optional, uses default)",
                            },
                        },
                        "required": ["dataset_id"],
                    },
                ),
                Tool(
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
                                "description": "Google Cloud project ID (optional, uses default)",
                            },
                        },
                        "required": ["table_id"],
                    },
                ),
                Tool(
                    name="validate_query",
                    description="Validate a SQL query without executing it",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "SQL query to validate"}
                        },
                        "required": ["query"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if not self.bigquery_client:
                    self.bigquery_client = BigQueryClient()

                if name == "execute_query":
                    return await self._execute_query(arguments)
                elif name == "list_datasets":
                    return await self._list_datasets(arguments)
                elif name == "list_tables":
                    return await self._list_tables(arguments)
                elif name == "get_table_schema":
                    return await self._get_table_schema(arguments)
                elif name == "validate_query":
                    return await self._validate_query(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")])

    async def _execute_query(self, arguments: dict[str, Any]) -> CallToolResult:
        """Execute a BigQuery SQL query."""
        query = arguments["query"]
        project_id = arguments.get("project_id")
        max_results = arguments.get("max_results", 1000)

        # Validate query
        if not validate_sql_query(query):
            return CallToolResult(
                content=[
                    TextContent(type="text", text="Error: Invalid or potentially unsafe SQL query")
                ]
            )

        try:
            results = await self.bigquery_client.execute_query(
                query, project_id=project_id, max_results=max_results
            )

            # Format results as JSON
            result_text = json.dumps(results, indent=2, default=str)

            return CallToolResult(
                content=[TextContent(type="text", text=f"Query Results:\n{result_text}")]
            )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Query execution error: {str(e)}")]
            )

    async def _list_datasets(self, arguments: dict[str, Any]) -> CallToolResult:
        """List BigQuery datasets."""
        project_id = arguments.get("project_id")

        try:
            datasets = await self.bigquery_client.list_datasets(project_id=project_id)
            result_text = json.dumps(datasets, indent=2)

            return CallToolResult(
                content=[TextContent(type="text", text=f"Datasets:\n{result_text}")]
            )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error listing datasets: {str(e)}")]
            )

    async def _list_tables(self, arguments: dict[str, Any]) -> CallToolResult:
        """List tables in a BigQuery dataset."""
        dataset_id = arguments["dataset_id"]
        project_id = arguments.get("project_id")

        try:
            tables = await self.bigquery_client.list_tables(
                dataset_id=dataset_id, project_id=project_id
            )
            result_text = json.dumps(tables, indent=2)

            return CallToolResult(
                content=[TextContent(type="text", text=f"Tables in {dataset_id}:\n{result_text}")]
            )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error listing tables: {str(e)}")]
            )

    async def _get_table_schema(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get BigQuery table schema."""
        table_id = arguments["table_id"]
        project_id = arguments.get("project_id")

        try:
            schema = await self.bigquery_client.get_table_schema(
                table_id=table_id, project_id=project_id
            )
            result_text = json.dumps(schema, indent=2)

            return CallToolResult(
                content=[TextContent(type="text", text=f"Schema for {table_id}:\n{result_text}")]
            )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting table schema: {str(e)}")]
            )

    async def _validate_query(self, arguments: dict[str, Any]) -> CallToolResult:
        """Validate a SQL query."""
        query = arguments["query"]

        try:
            is_valid = validate_sql_query(query)
            if is_valid:
                # Also validate with BigQuery dry run
                validation_result = await self.bigquery_client.validate_query(query)
                return CallToolResult(
                    content=[
                        TextContent(type="text", text=f"Query validation: {validation_result}")
                    ]
                )
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text", text="Query validation failed: Invalid or unsafe query"
                        )
                    ]
                )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Validation error: {str(e)}")]
            )

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting MCP BigQuery Server...")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-bigquery-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


async def main():
    """Main entry point."""
    setup_logging()

    server = MCPBigQueryServer()
    await server.run()


def main_sync():
    """Synchronous main entry point for script execution."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
