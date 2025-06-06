"""
Utility functions for the MCP BigQuery server.
"""

import logging
import re

# Comprehensive list of blocked SQL operations (DDL, DML, DCL, TCL)
BLOCKED_OPERATIONS = [
    # Data Definition Language (DDL)
    (r"\bcreate\s+", "CREATE operations"),
    (r"\bdrop\s+", "DROP operations"),
    (r"\balter\s+", "ALTER operations"),
    (r"\btruncate\s+", "TRUNCATE operations"),
    (r"\brename\s+", "RENAME operations"),
    
    # Data Manipulation Language (DML) - Write operations
    (r"\binsert\s+", "INSERT operations"),
    (r"\bupdate\s+", "UPDATE operations"),
    (r"\bdelete\s+", "DELETE operations"),
    (r"\bmerge\s+", "MERGE operations"),
    (r"\bupsert\s+", "UPSERT operations"),
    (r"\breplace\s+", "REPLACE operations"),
    
    # Data Control Language (DCL)
    (r"\bgrant\s+", "GRANT operations"),
    (r"\brevoke\s+", "REVOKE operations"),
    
    # Transaction Control Language (TCL)
    (r"\bcommit\b", "COMMIT operations"),
    (r"\brollback\b", "ROLLBACK operations"),
    (r"\bsavepoint\s+", "SAVEPOINT operations"),
    
    # Stored procedures and functions
    (r"\bexec\b", "EXEC operations"),
    (r"\bexecute\b", "EXECUTE operations"),
    (r"\bcall\s+", "CALL operations"),
    (r"\bsp_\w+", "stored procedure calls"),
    (r"\bxp_\w+", "extended stored procedure calls"),
    
    # BigQuery specific operations that could be dangerous
    (r"\bexport\s+data\b", "EXPORT DATA operations"),
    (r"\bload\s+data\b", "LOAD DATA operations"),
    (r"\bcopy\s+", "COPY operations"),
    
    # System and administrative commands
    (r"\bset\s+", "SET operations"),
    (r"\bdeclare\s+", "DECLARE operations"),
    (r"\buse\s+", "USE operations"),
    
    # Potentially dangerous functions
    (r"\bscript\b", "SCRIPT operations"),
    (r"\bjavascript\b", "JavaScript operations"),
    
    # Prevent nested queries that might contain write operations
    (r"\bselect\s+.*\b(?:insert|update|delete|create|drop|alter)\b", "nested write operations in SELECT"),
]


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
        logger.warning(f"Query validation failed: Query is not read-only. Query: {query_clean[:100]}...")
        return False

    # Check for any blocked operations using the shared list
    for pattern, operation_name in BLOCKED_OPERATIONS:
        if re.search(pattern, query_clean):
            logger.warning(f"Query validation failed: Contains blocked {operation_name}. Query: {query_clean[:100]}...")
            return False

    # Additional safety checks
    
    # Must start with SELECT or WITH (for CTEs that lead to SELECT)
    if not (query_clean.startswith("select") or query_clean.startswith("with")):
        logger.warning(f"Query validation failed: Query must start with SELECT or WITH. Query starts with: {query_clean[:20]}...")
        return False

    # Check for reasonable query length (prevent extremely long queries)
    if len(query) > 100000:  # 100KB limit
        logger.warning(f"Query validation failed: Query too long ({len(query)} characters, max 100000)")
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
        logger.warning(f"Query validation failed: Too many nested subqueries (depth: {max_depth}, max: 25)")
        return False

    # Check for excessive number of JOINs (potential performance issue)
    join_count = len(re.findall(r'\bjoin\b', query_clean))
    if join_count > 50:  # Arbitrary limit
        logger.warning(f"Query validation failed: Too many JOINs ({join_count}, max: 50)")
        return False

    # Ensure the query contains actual table references
    # (prevents queries like "SELECT 1" without FROM clause being too permissive)
    if not re.search(r'\bfrom\b', query_clean):
        # Allow simple expressions like "SELECT 1", "SELECT CURRENT_TIMESTAMP()", etc.
        # but be more restrictive about what functions are allowed
        allowed_simple_patterns = [
            r'^select\s+\d+$',  # SELECT 1, SELECT 123, etc.
            r'^select\s+current_timestamp\(\)$',
            r'^select\s+current_date\(\)$',
            r'^select\s+current_time\(\)$',
            r'^select\s+\'[^\']*\'$',  # SELECT 'string'
            r'^select\s+"[^"]*"$',     # SELECT "string"
        ]
        
        if not any(re.match(pattern, query_clean) for pattern in allowed_simple_patterns):
            logger.warning(f"Query validation failed: Query without FROM clause is not a simple allowed expression. Query: {query_clean}")
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
        logger.debug(f"Query is not read-only: Does not start with SELECT or WITH. Query: {query_clean[:50]}...")
        return False

    # Check for any write operations using the shared blocked operations list
    for operation_pattern, operation_name in BLOCKED_OPERATIONS:
        if re.search(operation_pattern, query_clean):
            logger.debug(f"Query is not read-only: Contains {operation_name}. Query: {query_clean[:50]}...")
            return False

    # Additional check: ensure WITH clauses only contain SELECT
    if query_clean.startswith("with"):
        # Split by WITH and check each CTE
        # This is a basic check - a more sophisticated parser would be better
        with_parts = re.split(r'\bwith\b', query_clean)[1:]  # Skip the first empty part
        for part in with_parts:
            # Look for the main SELECT after all CTEs
            if re.search(r'\bselect\b', part):
                # Check if there are any write operations in this part
                for operation_pattern, operation_name in BLOCKED_OPERATIONS:
                    if re.search(operation_pattern, part):
                        logger.debug(f"Query is not read-only: WITH clause contains {operation_name}. Query: {query_clean[:50]}...")
                        return False

    logger.debug(f"Query is read-only: {query_clean[:50]}...")
    return True
