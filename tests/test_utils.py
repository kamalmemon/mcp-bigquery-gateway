"""
Tests for utility functions.
"""

import pytest
from src.utils import (
    validate_sql_query,
    sanitize_table_name,
    format_bytes,
    extract_table_references,
    is_query_read_only
)


class TestValidateSqlQuery:
    """Test SQL query validation."""
    
    def test_valid_select_query(self):
        """Test that valid SELECT queries pass validation."""
        query = "SELECT * FROM users WHERE id = 1"
        assert validate_sql_query(query) is True
    
    def test_invalid_drop_query(self):
        """Test that DROP queries are rejected."""
        query = "DROP TABLE users"
        assert validate_sql_query(query) is False
    
    def test_invalid_delete_query(self):
        """Test that DELETE queries are rejected."""
        query = "DELETE FROM users WHERE id = 1"
        assert validate_sql_query(query) is False
    
    def test_invalid_insert_query(self):
        """Test that INSERT queries are rejected."""
        query = "INSERT INTO users (name) VALUES ('test')"
        assert validate_sql_query(query) is False
    
    def test_empty_query(self):
        """Test that empty queries are rejected."""
        assert validate_sql_query("") is False
        assert validate_sql_query(None) is False
    
    def test_query_with_comments(self):
        """Test that queries with comments are handled correctly."""
        query = """
        SELECT * FROM users 
        -- This is a comment
        WHERE id = 1
        """
        assert validate_sql_query(query) is True
    
    def test_complex_select_query(self):
        """Test that complex SELECT queries pass validation."""
        query = """
        SELECT u.name, p.title 
        FROM users u 
        JOIN posts p ON u.id = p.user_id 
        WHERE u.active = true 
        ORDER BY p.created_at DESC
        """
        assert validate_sql_query(query) is True


class TestSanitizeTableName:
    """Test table name sanitization."""
    
    def test_valid_table_name(self):
        """Test that valid table names are unchanged."""
        assert sanitize_table_name("users") == "users"
        assert sanitize_table_name("user_posts") == "user_posts"
        assert sanitize_table_name("dataset.table") == "dataset.table"
    
    def test_invalid_characters(self):
        """Test that invalid characters are removed."""
        assert sanitize_table_name("users; DROP TABLE") == "usersDROPTABLE"
        assert sanitize_table_name("users'") == "users"
    
    def test_empty_name(self):
        """Test that empty names return empty string."""
        assert sanitize_table_name("") == ""
        assert sanitize_table_name(None) == ""


class TestFormatBytes:
    """Test byte formatting."""
    
    def test_format_bytes(self):
        """Test byte formatting with various sizes."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(1073741824) == "1.0 GB"
        assert format_bytes(500) == "500.0 B"
    
    def test_format_none_bytes(self):
        """Test formatting None bytes."""
        assert format_bytes(None) == "Unknown"


class TestExtractTableReferences:
    """Test table reference extraction."""
    
    def test_simple_from_clause(self):
        """Test extracting table from simple FROM clause."""
        query = "SELECT * FROM users"
        tables = extract_table_references(query)
        assert "users" in tables
    
    def test_join_clauses(self):
        """Test extracting tables from JOIN clauses."""
        query = "SELECT * FROM users u JOIN posts p ON u.id = p.user_id"
        tables = extract_table_references(query)
        assert "users" in tables
        assert "posts" in tables
    
    def test_qualified_table_names(self):
        """Test extracting qualified table names."""
        query = "SELECT * FROM dataset.users"
        tables = extract_table_references(query)
        assert "dataset.users" in tables


class TestIsQueryReadOnly:
    """Test read-only query detection."""
    
    def test_select_query(self):
        """Test that SELECT queries are detected as read-only."""
        query = "SELECT * FROM users"
        assert is_query_read_only(query) is True
    
    def test_with_query(self):
        """Test that WITH queries are detected as read-only."""
        query = "WITH temp AS (SELECT * FROM users) SELECT * FROM temp"
        assert is_query_read_only(query) is True
    
    def test_insert_query(self):
        """Test that INSERT queries are not read-only."""
        query = "INSERT INTO users (name) VALUES ('test')"
        assert is_query_read_only(query) is False
    
    def test_update_query(self):
        """Test that UPDATE queries are not read-only."""
        query = "UPDATE users SET name = 'test' WHERE id = 1"
        assert is_query_read_only(query) is False 