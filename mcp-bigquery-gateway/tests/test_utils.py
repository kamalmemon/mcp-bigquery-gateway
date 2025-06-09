"""
Tests for utility functions.
"""

from src.utils import (
    extract_table_references,
    format_bytes,
    is_query_read_only,
    sanitize_table_name,
    validate_sql_query,
)


class TestValidateSqlQuery:
    """Test SQL query validation."""

    def test_valid_select_query(self):
        """Test that valid SELECT queries pass validation."""
        query = "SELECT * FROM users WHERE id = 1"
        assert validate_sql_query(query) is True

    def test_valid_select_with_joins(self):
        """Test that SELECT queries with JOINs pass validation."""
        query = """
        SELECT u.name, p.title
        FROM users u
        JOIN posts p ON u.id = p.user_id
        WHERE u.active = true
        ORDER BY p.created_at DESC
        """
        assert validate_sql_query(query) is True

    def test_valid_with_query(self):
        """Test that WITH (CTE) queries pass validation."""
        query = """
        WITH active_users AS (
            SELECT * FROM users WHERE active = true
        )
        SELECT * FROM active_users
        """
        assert validate_sql_query(query) is True

    def test_valid_simple_expressions(self):
        """Test that simple SELECT expressions pass validation."""
        assert validate_sql_query("SELECT 1") is True
        assert validate_sql_query("SELECT CURRENT_TIMESTAMP()") is True
        assert validate_sql_query("SELECT 'hello world'") is True

    # DDL Operations (should all fail)
    def test_invalid_create_table(self):
        """Test that CREATE TABLE queries are rejected."""
        query = "CREATE TABLE test (id INT, name STRING)"
        assert validate_sql_query(query) is False

    def test_invalid_drop_table(self):
        """Test that DROP TABLE queries are rejected."""
        query = "DROP TABLE users"
        assert validate_sql_query(query) is False

    def test_invalid_alter_table(self):
        """Test that ALTER TABLE queries are rejected."""
        query = "ALTER TABLE users ADD COLUMN email STRING"
        assert validate_sql_query(query) is False

    def test_invalid_truncate_table(self):
        """Test that TRUNCATE TABLE queries are rejected."""
        query = "TRUNCATE TABLE users"
        assert validate_sql_query(query) is False

    # DML Operations (should all fail)
    def test_invalid_insert_query(self):
        """Test that INSERT queries are rejected."""
        query = "INSERT INTO users (name) VALUES ('test')"
        assert validate_sql_query(query) is False

    def test_invalid_update_query(self):
        """Test that UPDATE queries are rejected."""
        query = "UPDATE users SET name = 'test' WHERE id = 1"
        assert validate_sql_query(query) is False

    def test_invalid_delete_query(self):
        """Test that DELETE queries are rejected."""
        query = "DELETE FROM users WHERE id = 1"
        assert validate_sql_query(query) is False

    def test_invalid_merge_query(self):
        """Test that MERGE queries are rejected."""
        query = "MERGE users USING new_users ON users.id = new_users.id"
        assert validate_sql_query(query) is False

    # DCL Operations (should all fail)
    def test_invalid_grant_query(self):
        """Test that GRANT queries are rejected."""
        query = "GRANT SELECT ON users TO user@domain.com"
        assert validate_sql_query(query) is False

    def test_invalid_revoke_query(self):
        """Test that REVOKE queries are rejected."""
        query = "REVOKE SELECT ON users FROM user@domain.com"
        assert validate_sql_query(query) is False

    # Procedure calls (should all fail)
    def test_invalid_exec_query(self):
        """Test that EXEC queries are rejected."""
        query = "EXEC sp_procedure"
        assert validate_sql_query(query) is False

    def test_invalid_call_query(self):
        """Test that CALL queries are rejected."""
        query = "CALL my_procedure()"
        assert validate_sql_query(query) is False

    # BigQuery specific operations (should all fail)
    def test_invalid_export_data(self):
        """Test that EXPORT DATA queries are rejected."""
        query = "EXPORT DATA OPTIONS(uri='gs://bucket/file') AS SELECT * FROM users"
        assert validate_sql_query(query) is False

    def test_invalid_load_data(self):
        """Test that LOAD DATA queries are rejected."""
        query = "LOAD DATA INTO users FROM FILES('gs://bucket/file')"
        assert validate_sql_query(query) is False

    # Edge cases and security tests
    def test_invalid_nested_write_operations(self):
        """Test that nested write operations in SELECT are rejected."""
        query = "SELECT * FROM (INSERT INTO users VALUES (1, 'test'))"
        assert validate_sql_query(query) is False

    def test_invalid_with_write_operations(self):
        """Test that WITH clauses containing write operations are rejected."""
        query = """
        WITH temp AS (
            INSERT INTO users VALUES (1, 'test')
        )
        SELECT * FROM temp
        """
        assert validate_sql_query(query) is False

    def test_invalid_case_variations(self):
        """Test that case variations of blocked operations are rejected."""
        assert validate_sql_query("Insert Into users VALUES (1)") is False
        assert validate_sql_query("UPDATE users set name='test'") is False
        assert validate_sql_query("Delete From users") is False
        assert validate_sql_query("CREATE table test (id int)") is False

    def test_invalid_with_comments(self):
        """Test that blocked operations with comments are still rejected."""
        query = """
        /* This is a comment */
        INSERT INTO users (name) VALUES ('test')
        -- Another comment
        """
        assert validate_sql_query(query) is False

    def test_empty_and_invalid_inputs(self):
        """Test that empty and invalid inputs are rejected."""
        assert validate_sql_query("") is False
        assert validate_sql_query(None) is False
        assert validate_sql_query("   ") is False
        assert validate_sql_query("INVALID SQL") is False

    def test_query_length_limits(self):
        """Test that extremely long queries are rejected."""
        # Create a very long query
        long_query = "SELECT * FROM users WHERE " + " OR ".join([f"id = {i}" for i in range(10000)])
        assert validate_sql_query(long_query) is False

    def test_excessive_nesting(self):
        """Test that queries with excessive nesting are rejected."""
        # Create a deeply nested query
        nested_query = "SELECT * FROM users WHERE id IN (" * 30 + "SELECT 1" + ")" * 30
        assert validate_sql_query(nested_query) is False

    def test_excessive_joins(self):
        """Test that queries with too many JOINs are rejected."""
        # Create a query with many JOINs
        joins = " ".join([f"JOIN table{i} t{i} ON t{i-1}.id = t{i}.id" for i in range(1, 60)])
        query = f"SELECT * FROM table0 t0 {joins}"
        assert validate_sql_query(query) is False


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
        query = "select * from users"
        assert is_query_read_only(query) is True

    def test_with_query(self):
        """Test that WITH queries are detected as read-only."""
        query = "with temp as (select * from users) select * from temp"
        assert is_query_read_only(query) is True

    def test_insert_query(self):
        """Test that INSERT queries are not read-only."""
        query = "insert into users (name) values ('test')"
        assert is_query_read_only(query) is False

    def test_update_query(self):
        """Test that UPDATE queries are not read-only."""
        query = "update users set name = 'test' where id = 1"
        assert is_query_read_only(query) is False

    def test_delete_query(self):
        """Test that DELETE queries are not read-only."""
        query = "delete from users where id = 1"
        assert is_query_read_only(query) is False

    def test_create_query(self):
        """Test that CREATE queries are not read-only."""
        query = "create table test (id int)"
        assert is_query_read_only(query) is False

    def test_non_select_start(self):
        """Test that queries not starting with SELECT or WITH are not read-only."""
        query = "show tables"
        assert is_query_read_only(query) is False
