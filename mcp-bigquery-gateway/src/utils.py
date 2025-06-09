"""
Utility functions for the MCP BigQuery server.
"""

import logging
import re

# Essential blocked SQL operations for safety
BLOCKED_OPERATIONS = [
    # Data modification operations
    (r"\b(create|drop|alter|truncate|rename)\s+", "DDL operations"),
    (r"\b(insert|update|delete|merge|replace)\s+", "DML operations"),
    (r"\b(grant|revoke)\s+", "DCL operations"),
    (r"\b(exec|execute|call)\b", "procedure calls"),
    (r"\bscript\b", "script operations"),
]


def setup_logging(level: str = "WARNING") -> None:
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
    Validate SQL query to ensure only SELECT queries are allowed.

    This function performs strict validation to only allow read-only SELECT operations.
    All DDL (Data Definition Language) and DML (Data Manipulation Language) operations
    are blocked to ensure data safety.

    Args:
        query: SQL query string to validate

    Returns:
        True if query is a valid SELECT query, False otherwise
    """
    logger = logging.getLogger(__name__)

    if not query or not isinstance(query, str):
        logger.warning("Query validation failed: Query is empty or not a string")
        return False

    # Convert to lowercase for checking
    query_lower = query.lower().strip()

    # Remove comments and extra whitespace
    query_clean = re.sub(r"--.*$", "", query_lower, flags=re.MULTILINE)
    query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)
    query_clean = " ".join(query_clean.split())

    # First check: Must be a read-only query
    if not is_query_read_only(query_clean):
        logger.warning(
            f"Query validation failed: Query is not read-only. Query: {query_clean[:100]}..."
        )
        return False

    # Check for any blocked operations using the shared list
    for pattern, operation_name in BLOCKED_OPERATIONS:
        if re.search(pattern, query_clean):
            logger.warning(
                f"Query validation failed: Contains blocked {operation_name}. "
                f"Query: {query_clean[:50]}..."
            )
            return False

    # Additional safety checks

    # Must start with SELECT or WITH (for CTEs that lead to SELECT)
    if not (query_clean.startswith("select") or query_clean.startswith("with")):
        logger.warning(
            f"Query validation failed: Query must start with SELECT or WITH. "
            f"Query starts with: {query_clean[:20]}..."
        )
        return False

    # Check for reasonable query length (prevent extremely long queries)
    if len(query) > 100000:  # 100KB limit
        logger.warning(
            f"Query validation failed: Query too long ({len(query)} characters, max 100000)"
        )
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

    if max_depth > 25:  # Limit nested queries
        logger.warning(
            f"Query validation failed: Too many nested subqueries (depth: {max_depth}, max: 25)"
        )
        return False

    # Check for excessive number of JOINs (potential performance issue)
    join_count = len(re.findall(r"\bjoin\b", query_clean))
    if join_count > 50:  # Arbitrary limit
        logger.warning(f"Query validation failed: Too many JOINs ({join_count}, max: 50)")
        return False

    # Ensure the query contains actual table references
    # (prevents queries like "SELECT 1" without FROM clause being too permissive)
    if not re.search(r"\bfrom\b", query_clean):
        # Allow simple expressions like "SELECT 1", "SELECT CURRENT_TIMESTAMP()", etc.
        # but be more restrictive about what functions are allowed
        allowed_simple_patterns = [
            r"^select\s+\d+$",  # SELECT 1, SELECT 123, etc.
            r"^select\s+current_timestamp\(\)$",
            r"^select\s+current_date\(\)$",
            r"^select\s+current_time\(\)$",
            r"^select\s+\'[^\']*\'$",  # SELECT 'string'
            r'^select\s+"[^"]*"$',  # SELECT "string"
        ]

        if not any(re.match(pattern, query_clean) for pattern in allowed_simple_patterns):
            logger.warning(
                f"Query validation failed: Query without FROM clause "
                f"is not a simple allowed expression. Query: {query_clean}"
            )
            return False

    logger.info(f"Query validation passed: {query_clean[:100]}...")
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
        query: SQL query string (should be cleaned/normalized)

    Returns:
        True if query appears to be read-only, False otherwise
    """
    logger = logging.getLogger(__name__)
    query_clean = query.strip()

    # Must start with SELECT or WITH (for CTEs that lead to SELECT)
    if not (query_clean.startswith("select") or query_clean.startswith("with")):
        logger.debug(
            f"Query is not read-only: Does not start with SELECT or WITH. "
            f"Query: {query_clean[:50]}..."
        )
        return False

    # Check for any write operations using the shared blocked operations list
    for operation_pattern, operation_name in BLOCKED_OPERATIONS:
        if re.search(operation_pattern, query_clean):
            logger.debug(
                f"Query is not read-only: Contains {operation_name}. Query: {query_clean[:50]}..."
            )
            return False

    # Additional check: ensure WITH clauses only contain SELECT
    if query_clean.startswith("with"):
        # Split by WITH and check each CTE
        # This is a basic check - a more sophisticated parser would be better
        with_parts = re.split(r"\bwith\b", query_clean)[1:]  # Skip the first empty part
        for part in with_parts:
            # Look for the main SELECT after all CTEs
            if re.search(r"\bselect\b", part):
                # Check if there are any write operations in this part
                for operation_pattern, operation_name in BLOCKED_OPERATIONS:
                    if re.search(operation_pattern, part):
                        logger.debug(
                            f"Query is not read-only: WITH clause contains {operation_name}. "
                            f"Query: {query_clean[:50]}..."
                        )
                        return False

    logger.debug(f"Query is read-only: {query_clean[:50]}...")
    return True
