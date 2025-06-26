#!/usr/bin/env python3
"""
Tests for BigQuery Client functionality
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bigquery_client import BigQueryClient


class TestBigQueryClient:
    """Test BigQuery client functionality."""
    
    @pytest.fixture
    def mock_bigquery_client(self):
        """Create a mock BigQuery client for testing."""
        with patch('bigquery_client.bigquery.Client') as mock_client_class:
            with patch('bigquery_client.service_account') as mock_service_account:
                # Mock the client instance
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.get_service_account_email.return_value = "test@test.com"
                mock_client.project = "test-project"
                
                # Create BigQuery client instance
                client = BigQueryClient(project_id="test-project")
                yield client, mock_client

    def test_initialization_with_default_max_workers(self, mock_bigquery_client):
        """Test that BigQuery client initializes with dynamic max_workers."""
        client, _ = mock_bigquery_client
        
        # Should use ThreadPoolExecutor default logic: min(32, (cpu_count + 4))
        expected_max_workers = min(32, (os.cpu_count() or 1) + 4)
        assert client.executor._max_workers == expected_max_workers

    def test_default_max_bytes_billed_constant(self, mock_bigquery_client):
        """Test that the default max bytes billed constant is set correctly."""
        client, _ = mock_bigquery_client
        
        # Should be 500GB in bytes
        expected_bytes = 500 * 1024 * 1024 * 1024
        assert client.DEFAULT_MAX_BYTES_BILLED == expected_bytes

    @pytest.mark.asyncio
    async def test_execute_query_with_default_max_bytes_billed(self, mock_bigquery_client):
        """Test execute_query uses default max_bytes_billed when not specified."""
        client, mock_client = mock_bigquery_client
        
        # Mock query job and results
        mock_query_job = MagicMock()
        mock_results = MagicMock()
        mock_results.total_rows = 1
        mock_results.schema = []
        mock_results.__iter__ = lambda x: iter([{"test": "value"}])
        
        mock_query_job.result.return_value = mock_results
        mock_client.query.return_value = mock_query_job
        
        # Execute query without specifying max_bytes_billed
        result = await client.execute_query("SELECT 1")
        
        # Check that query was called with default max_bytes_billed
        call_args = mock_client.query.call_args
        job_config = call_args[1]['job_config']
        assert job_config.maximum_bytes_billed == client.DEFAULT_MAX_BYTES_BILLED

    @pytest.mark.asyncio
    async def test_execute_query_with_custom_max_bytes_billed(self, mock_bigquery_client):
        """Test execute_query uses custom max_bytes_billed when specified."""
        client, mock_client = mock_bigquery_client
        
        # Mock query job and results
        mock_query_job = MagicMock()
        mock_results = MagicMock()
        mock_results.total_rows = 1
        mock_results.schema = []
        mock_results.__iter__ = lambda x: iter([{"test": "value"}])
        
        mock_query_job.result.return_value = mock_results
        mock_client.query.return_value = mock_query_job
        
        # Execute query with custom max_bytes_billed
        custom_limit = 1000000000  # 1GB
        result = await client.execute_query("SELECT 1", max_bytes_billed=custom_limit)
        
        # Check that query was called with custom max_bytes_billed
        call_args = mock_client.query.call_args
        job_config = call_args[1]['job_config']
        assert job_config.maximum_bytes_billed == custom_limit

    @pytest.mark.asyncio
    async def test_get_job_details_success(self, mock_bigquery_client):
        """Test get_job_details method returns correct job information."""
        client, mock_client = mock_bigquery_client
        
        # Mock job object
        mock_job = MagicMock()
        mock_job.job_id = "test_job_123"
        mock_job.state = "DONE"
        mock_job.job_type = "QUERY"
        mock_job.created = MagicMock()
        mock_job.created.isoformat.return_value = "2023-01-01T10:00:00"
        mock_job.started = MagicMock()
        mock_job.started.isoformat.return_value = "2023-01-01T10:00:01"
        mock_job.ended = MagicMock()
        mock_job.ended.isoformat.return_value = "2023-01-01T10:05:00"
        mock_job.user_email = "test@example.com"
        mock_job.total_bytes_processed = 1048576
        mock_job.total_bytes_billed = 10485760
        mock_job.total_slot_ms = 5000
        mock_job.query = "SELECT * FROM test_table"
        
        # Mock job config
        mock_job_config = MagicMock()
        mock_job_config.dry_run = False
        mock_job_config.use_query_cache = True
        mock_job_config.maximum_bytes_billed = 500 * 1024 * 1024 * 1024
        mock_job.job_config = mock_job_config
        
        mock_client.get_job.return_value = mock_job
        
        # Call get_job_details
        result = await client.get_job_details("test_job_123")
        
        # Verify the result structure
        assert result["job_id"] == "test_job_123"
        assert result["state"] == "DONE"
        assert result["job_type"] == "QUERY"
        assert result["created"] == "2023-01-01T10:00:00"
        assert result["started"] == "2023-01-01T10:00:01"
        assert result["ended"] == "2023-01-01T10:05:00"
        assert result["user_email"] == "test@example.com"
        assert result["total_bytes_processed"] == 1048576
        assert result["total_bytes_billed"] == 10485760
        assert result["total_slot_ms"] == 5000
        assert result["query"] == "SELECT * FROM test_table"
        assert result["dry_run"] == False
        assert result["use_query_cache"] == True
        assert result["maximum_bytes_billed"] == 500 * 1024 * 1024 * 1024
        
        # Verify get_job was called with correct job_id
        mock_client.get_job.assert_called_once_with("test_job_123")

    @pytest.mark.asyncio
    async def test_get_job_details_with_project_id(self, mock_bigquery_client):
        """Test get_job_details with different project_id creates new client."""
        client, mock_client = mock_bigquery_client
        
        with patch('bigquery_client.bigquery.Client') as mock_client_class:
            # Mock the new client for different project
            mock_new_client = MagicMock()
            mock_client_class.return_value = mock_new_client
            
            # Mock job object
            mock_job = MagicMock()
            mock_job.job_id = "test_job_123"
            mock_job.state = "DONE"
            mock_job.job_type = "QUERY"
            mock_job.created = None
            mock_job.started = None
            mock_job.ended = None
            mock_job.user_email = "test@example.com"
            mock_job.query = "SELECT 1"
            
            mock_new_client.get_job.return_value = mock_job
            
            # Call get_job_details with different project_id
            result = await client.get_job_details("test_job_123", project_id="different-project")
            
            # Verify new client was created with different project
            mock_client_class.assert_called_once_with(project="different-project")
            mock_new_client.get_job.assert_called_once_with("test_job_123")

    @pytest.mark.asyncio
    async def test_get_job_details_handles_missing_attributes(self, mock_bigquery_client):
        """Test get_job_details handles jobs with missing optional attributes."""
        client, mock_client = mock_bigquery_client
        
        # Create a simple mock that only has the required attributes
        class MinimalJob:
            def __init__(self):
                self.job_id = "test_job_123"
                self.state = "DONE"
                self.job_type = "QUERY"
                self.user_email = "test@example.com"
                # Note: missing created, started, ended, query, job_config
                # and getattr will return None for total_bytes_* attributes
        
        mock_job = MinimalJob()
        mock_client.get_job.return_value = mock_job
        
        # Call get_job_details
        result = await client.get_job_details("test_job_123")
        
        # Verify it handles missing attributes gracefully
        assert result["job_id"] == "test_job_123"
        assert result["state"] == "DONE"
        assert result["job_type"] == "QUERY"
        assert result["user_email"] == "test@example.com"
        assert result["created"] is None
        assert result["started"] is None
        assert result["ended"] is None
        assert result["total_bytes_processed"] is None
        assert result["total_bytes_billed"] is None
        assert result["total_slot_ms"] is None
        assert result["query"] is None

    @pytest.mark.asyncio
    async def test_execute_query_zero_max_bytes_uses_default(self, mock_bigquery_client):
        """Test that passing 0 for max_bytes_billed uses default (via 'or' operator)."""
        client, mock_client = mock_bigquery_client
        
        # Mock query job and results
        mock_query_job = MagicMock()
        mock_results = MagicMock()
        mock_results.total_rows = 1
        mock_results.schema = []
        mock_results.__iter__ = lambda x: iter([{"test": "value"}])
        
        mock_query_job.result.return_value = mock_results
        mock_client.query.return_value = mock_query_job
        
        # Execute query with max_bytes_billed=0 (should use default)
        result = await client.execute_query("SELECT 1", max_bytes_billed=0)
        
        # Check that query was called with default max_bytes_billed (since 0 is falsy)
        call_args = mock_client.query.call_args
        job_config = call_args[1]['job_config']
        assert job_config.maximum_bytes_billed == client.DEFAULT_MAX_BYTES_BILLED 