"""
Utility functions for the MCP BigQuery server.
"""

import logging
import re


def setup_logging(level: str = "INFO") -> None:
    """
    Set up logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def validate_sql_query(query: str) -> bool:
    """
    Validate SQL query for basic safety checks.

    This function performs basic validation to prevent potentially dangerous
    SQL operations. It's not foolproof but provides a first line of defense.

    Args:
        query: SQL query string to validate

    Returns:
        True if query passes basic validation, False otherwise
    """
    if not query or not isinstance(query, str):
        return False

    # Convert to lowercase for checking
    query_lower = query.lower().strip()

    # Remove comments and extra whitespace
    query_clean = re.sub(r"--.*$", "", query_lower, flags=re.MULTILINE)
    query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)
    query_clean = " ".join(query_clean.split())

    # Dangerous operations to block
    dangerous_patterns = [
        r"\bdrop\s+table\b",
        r"\bdrop\s+database\b",
        r"\bdrop\s+schema\b",
        r"\bdelete\s+from\b",
        r"\btruncate\s+table\b",
        r"\balter\s+table\b",
        r"\bcreate\s+table\b",
        r"\binsert\s+into\b",
        r"\bupdate\s+.*\s+set\b",
        r"\bgrant\s+",
        r"\brevoke\s+",
        r"\bexec\b",
        r"\bexecute\b",
        r"\bsp_\w+",  # Stored procedures
        r"\bxp_\w+",  # Extended stored procedures
    ]

    # Check for dangerous patterns
    for pattern in dangerous_patterns:
        if re.search(pattern, query_clean):
            return False

    # Must contain SELECT (basic requirement for read-only queries)
    if not re.search(r"\bselect\b", query_clean):
        return False

    # Check for reasonable query length (prevent extremely long queries)
    if len(query) > 50000:  # 50KB limit
        return False

    # Check for excessive nested subqueries (basic DoS prevention)
    paren_depth = 0
    max_depth = 0
    for char in query_clean:
        if char == "(":
            paren_depth += 1
            max_depth = max(max_depth, paren_depth)
        elif char == ")":
            paren_depth -= 1

    if max_depth > 20:  # Arbitrary limit for nested queries
        return False

    return True


def sanitize_table_name(table_name: str) -> str:
    """
    Sanitize table name to prevent injection attacks.

    Args:
        table_name: Table name to sanitize

    Returns:
        Sanitized table name
    """
    if not table_name:
        return ""

    # Allow only alphanumeric characters, underscores, dots, and hyphens
    sanitized = re.sub(r"[^a-zA-Z0-9_.-]", "", table_name)

    # Ensure it doesn't start with a number or special character
    if sanitized and not sanitized[0].isalpha():
        sanitized = "table_" + sanitized

    return sanitized


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes into human-readable string.

    Args:
        bytes_value: Number of bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if bytes_value is None:
        return "Unknown"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def extract_table_references(query: str) -> set[str]:
    """
    Extract table references from a SQL query.

    This is a basic implementation that looks for common table reference patterns.

    Args:
        query: SQL query string

    Returns:
        Set of table names referenced in the query
    """
    tables = set()

    # Convert to lowercase for pattern matching
    query_lower = query.lower()

    # Remove comments
    query_clean = re.sub(r"--.*$", "", query_lower, flags=re.MULTILINE)
    query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)

    # Pattern to match table references after FROM and JOIN
    patterns = [
        r'\bfrom\s+([`"]?[\w.-]+[`"]?)',
        r'\bjoin\s+([`"]?[\w.-]+[`"]?)',
        r'\binner\s+join\s+([`"]?[\w.-]+[`"]?)',
        r'\bleft\s+join\s+([`"]?[\w.-]+[`"]?)',
        r'\bright\s+join\s+([`"]?[\w.-]+[`"]?)',
        r'\bfull\s+join\s+([`"]?[\w.-]+[`"]?)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, query_clean)
        for match in matches:
            # Remove backticks and quotes
            table_name = match.strip('`"')
            if table_name:
                tables.add(table_name)

    return tables


def is_query_read_only(query: str) -> bool:
    """
    Check if a query is read-only (SELECT only).

    Args:
        query: SQL query string

    Returns:
        True if query appears to be read-only, False otherwise
    """
    query_lower = query.lower().strip()

    # Remove comments
    query_clean = re.sub(r"--.*$", "", query_lower, flags=re.MULTILINE)
    query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)
    query_clean = query_clean.strip()

    # Check if it starts with SELECT or WITH (for CTEs)
    if query_clean.startswith("select") or query_clean.startswith("with"):
        # Make sure it doesn't contain any write operations
        write_operations = [
            "insert",
            "update",
            "delete",
            "drop",
            "create",
            "alter",
            "truncate",
            "grant",
            "revoke",
        ]

        for operation in write_operations:
            if re.search(rf"\b{operation}\b", query_clean):
                return False

        return True

    return False
