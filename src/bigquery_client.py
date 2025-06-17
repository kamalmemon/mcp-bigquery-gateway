"""
BigQuery Client

A wrapper around the Google Cloud BigQuery client with async support.
"""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Async wrapper for Google Cloud BigQuery client."""

    def __init__(self, project_id: str | None = None, credentials_path: str | None = None):
        """
        Initialize BigQuery client.

        Args:
            project_id: Google Cloud project ID. If None, uses default from environment.
            credentials_path: Path to service account JSON file. If None, uses ADC.
        """
        # Use ThreadPoolExecutor default logic for I/O-bound operations
        # min(32, (os.cpu_count() or 1) + 4) adapts to system capabilities
        max_workers = min(32, (os.cpu_count() or 1) + 4)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the BigQuery client with appropriate credentials."""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                # Use service account credentials if provided
                logger.info(f"Using service account credentials from {self.credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = bigquery.Client(
                    credentials=credentials, project=self.project_id or credentials.project_id
                )
            else:
                # Use Application Default Credentials (recommended)
                logger.info("Using Application Default Credentials")
                self.client = bigquery.Client(project=self.project_id)

            # Test the connection
            self.client.get_service_account_email()
            logger.info(f"Successfully connected to BigQuery with project: {self.client.project}")

        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {str(e)}")
            logger.error(
                "Please ensure you are authenticated with Google Cloud. "
                "Run 'make auth' or 'gcloud auth application-default login'"
            )
            raise

    async def execute_query(
        self, query: str, project_id: str | None = None, max_results: int = 1000
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query to execute
            project_id: Project ID to use (optional)
            max_results: Maximum number of results to return

        Returns:
            List of dictionaries representing query results
        """

        def _run_query():
            job_config = bigquery.QueryJobConfig()
            job_config.maximum_bytes_billed = 100 * 1024 * 1024  # 100 MB limit

            client = self.client
            if project_id:
                # Create a new client for different project if needed
                client = bigquery.Client(project=project_id)

            query_job = client.query(query, job_config=job_config)
            results = query_job.result(max_results=max_results)

            # Convert results to list of dictionaries
            rows = []
            for row in results:
                rows.append(dict(row))

            return {
                "rows": rows,
                "total_rows": results.total_rows,
                "schema": [
                    {"name": field.name, "type": field.field_type} for field in results.schema
                ],
            }

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, _run_query)
            logger.info(f"Query executed successfully, returned {len(result['rows'])} rows")
            return result

        except GoogleCloudError as e:
            logger.error(f"BigQuery error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query: {str(e)}")
            raise

    async def validate_query(self, query: str, project_id: str | None = None) -> dict[str, Any]:
        """
        Validate a SQL query using dry run.

        Args:
            query: SQL query to validate
            project_id: Project ID to use (optional)

        Returns:
            Validation result dictionary
        """

        def _validate():
            job_config = bigquery.QueryJobConfig()
            job_config.dry_run = True
            job_config.use_query_cache = False

            client = self.client
            if project_id:
                client = bigquery.Client(project=project_id)

            query_job = client.query(query, job_config=job_config)

            return {
                "valid": True,
                "total_bytes_processed": query_job.total_bytes_processed,
                "total_bytes_billed": query_job.total_bytes_billed,
                "schema": (
                    [{"name": field.name, "type": field.field_type} for field in query_job.schema]
                    if query_job.schema
                    else []
                ),
            }

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, _validate)
            logger.info("Query validation successful")
            return result

        except GoogleCloudError as e:
            logger.error(f"Query validation failed: {str(e)}")
            return {"valid": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error validating query: {str(e)}")
            return {"valid": False, "error": str(e)}

    async def list_datasets(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """
        List all datasets in a project.

        Args:
            project_id: Project ID to use (optional)

        Returns:
            List of dataset information dictionaries
        """

        def _list_datasets():
            client = self.client
            if project_id:
                client = bigquery.Client(project=project_id)

            datasets = client.list_datasets()

            result = []
            for dataset in datasets:
                result.append(
                    {
                        "dataset_id": dataset.dataset_id,
                        "project": dataset.project,
                        "full_dataset_id": dataset.full_dataset_id,
                        "friendly_name": getattr(dataset, "friendly_name", None),
                        "labels": getattr(dataset, "labels", {}),
                    }
                )

            return result

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, _list_datasets)
            logger.info(f"Listed {len(result)} datasets")
            return result

        except GoogleCloudError as e:
            logger.error(f"Error listing datasets: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing datasets: {str(e)}")
            raise

    async def list_tables(
        self, dataset_id: str, project_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List all tables in a dataset.

        Args:
            dataset_id: Dataset ID to list tables from
            project_id: Project ID to use (optional)

        Returns:
            List of table information dictionaries
        """

        def _list_tables():
            client = self.client
            if project_id:
                client = bigquery.Client(project=project_id)

            dataset_ref = client.dataset(dataset_id)
            tables = client.list_tables(dataset_ref)

            result = []
            for table in tables:
                result.append(
                    {
                        "table_id": table.table_id,
                        "dataset_id": table.dataset_id,
                        "project": table.project,
                        "full_table_id": table.full_table_id,
                        "table_type": table.table_type,
                        "creation_time": (
                            table.creation_time.isoformat()
                            if hasattr(table, "creation_time") and table.creation_time
                            else None
                        ),
                        "expiration_time": (
                            table.expiration_time.isoformat()
                            if hasattr(table, "expiration_time") and table.expiration_time
                            else None
                        ),
                        "friendly_name": getattr(table, "friendly_name", None),
                        "labels": getattr(table, "labels", {}),
                    }
                )

            return result

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, _list_tables)
            logger.info(f"Listed {len(result)} tables in dataset {dataset_id}")
            return result

        except GoogleCloudError as e:
            logger.error(f"Error listing tables: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing tables: {str(e)}")
            raise

    async def get_table_schema(
        self, table_id: str, project_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get the schema of a table.

        Args:
            table_id: Table ID in format 'dataset.table'
            project_id: Project ID to use (optional)

        Returns:
            Table schema information dictionary
        """

        def _get_schema():
            client = self.client
            if project_id:
                client = bigquery.Client(project=project_id)

            # Parse table_id
            if "." in table_id:
                dataset_id, table_name = table_id.split(".", 1)
            else:
                raise ValueError("table_id must be in format 'dataset.table'")

            table_ref = client.dataset(dataset_id).table(table_name)
            table = client.get_table(table_ref)

            schema_fields = []
            for field in table.schema:
                schema_fields.append(
                    {
                        "name": field.name,
                        "field_type": field.field_type,
                        "mode": field.mode,
                        "description": field.description,
                    }
                )

            return {
                "table_id": table.table_id,
                "dataset_id": table.dataset_id,
                "project": table.project,
                "full_table_id": table.full_table_id,
                "created": table.created.isoformat() if table.created else None,
                "modified": table.modified.isoformat() if table.modified else None,
                "num_rows": table.num_rows,
                "num_bytes": table.num_bytes,
                "description": table.description,
                "schema": schema_fields,
            }

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, _get_schema)
            logger.info(f"Retrieved schema for table {table_id}")
            return result

        except GoogleCloudError as e:
            logger.error(f"Error getting table schema: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting table schema: {str(e)}")
            raise

    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)
