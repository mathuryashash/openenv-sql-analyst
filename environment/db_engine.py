# environment/db_engine.py
# SQLite Database Engine with Security Safeguards
# Implements: Mutation Blocker, OOM Protection, Timeout Wrapper

import re
import sqlite3
import signal
import os
from typing import Tuple, Optional
from contextlib import contextmanager
from pathlib import Path


# Regex pattern for blocking destructive SQL operations
MUTATION_PATTERN = re.compile(
    r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE)\b',
    re.IGNORECASE
)

# Query execution timeout in seconds
QUERY_TIMEOUT = 2.0

# Maximum rows to fetch (OOM protection)
MAX_FETCH_ROWS = 50


class TimeoutError(Exception):
    """Custom exception for query timeout."""
    pass


@contextmanager
def timeout_handler(seconds: float):
    """
    Context manager for query timeout.
    Note: signal.alarm only works on Unix. On Windows, we use a simpler approach.
    """
    # On Windows, signal.SIGALRM is not available
    # We implement a basic timeout check instead
    if os.name == 'nt':
        # Windows: No signal-based timeout, rely on sqlite3 timeout
        yield
    else:
        def handler(signum, frame):
            raise TimeoutError(f"Query execution exceeded {seconds} seconds timeout")
        
        old_handler = signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)


class DatabaseEngine:
    """
    SQLite Database Engine with security safeguards.
    
    Features:
    - In-memory SQLite database (:memory: mode)
    - Mutation Blocker: Regex-based blocking of INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE
    - OOM Protection: cursor.fetchmany(50), never fetchall()
    - Timeout Wrapper: 2.0-second timeout for query execution
    - Stringified errors: Never raises Python exceptions to caller
    """
    
    def __init__(self):
        """Initialize the database engine with an in-memory SQLite database."""
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._schema_cache: Optional[str] = None
    
    def initialize(self) -> str:
        """
        Initialize a clean in-memory SQLite database and load mock data.
        
        Returns:
            str: Success message or error string
        """
        try:
            # Close existing connection if any
            self.close()
            
            # Create new in-memory database
            self.connection = sqlite3.connect(
                ':memory:',
                timeout=QUERY_TIMEOUT,
                check_same_thread=False
            )
            self.cursor = self.connection.cursor()
            
            # Load mock data from SQL file
            mock_data_path = Path(__file__).parent.parent / 'data' / 'mock_data.sql'
            
            if mock_data_path.exists():
                with open(mock_data_path, 'r') as f:
                    sql_script = f.read()
                self.cursor.executescript(sql_script)
                self.connection.commit()
            else:
                return f"Error: Mock data file not found at {mock_data_path}"
            
            # Cache schema info
            self._schema_cache = self._get_schema_info()
            
            return "Database initialized successfully"
            
        except Exception as e:
            return f"Error initializing database: {str(e)}"
    
    def _get_schema_info(self) -> str:
        """
        Get database schema information for the agent.
        
        Returns:
            str: Formatted schema information
        """
        if not self.cursor:
            return "Error: Database not initialized"
        
        try:
            # Get all table names
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in self.cursor.fetchmany(MAX_FETCH_ROWS)]
            
            schema_parts = ["DATABASE SCHEMA:", "=" * 50]
            
            for table in tables:
                schema_parts.append(f"\nTable: {table}")
                schema_parts.append("-" * 30)
                
                # Get column info using PRAGMA
                self.cursor.execute(f"PRAGMA table_info({table})")
                columns = self.cursor.fetchmany(MAX_FETCH_ROWS)
                
                for col in columns:
                    col_id, name, col_type, not_null, default, pk = col
                    pk_marker = " [PRIMARY KEY]" if pk else ""
                    null_marker = " NOT NULL" if not_null else ""
                    schema_parts.append(f"  - {name}: {col_type}{null_marker}{pk_marker}")
            
            return "\n".join(schema_parts)
            
        except Exception as e:
            return f"Error getting schema: {str(e)}"
    
    def get_schema(self) -> str:
        """
        Get cached schema information.
        
        Returns:
            str: Schema information string
        """
        if self._schema_cache:
            return self._schema_cache
        return self._get_schema_info()
    
    def check_mutation(self, query: str) -> Optional[str]:
        """
        Check if query contains mutation operations.
        
        Args:
            query: SQL query string
            
        Returns:
            Optional[str]: Error message if mutation detected, None otherwise
        """
        match = MUTATION_PATTERN.search(query)
        if match:
            matched = match.group(1).upper()
            return (
                f"DESTRUCTIVE_ACTION_BLOCKED: {matched} operations are not allowed. "
                f"This environment is read-only. Only SELECT queries are permitted."
            )
        return None
    
    def execute_query(self, query: str) -> Tuple[str, bool]:
        """
        Execute a SQL query with all safety measures.
        
        Args:
            query: SQL query string
            
        Returns:
            Tuple[str, bool]: (result_string, is_error)
                - result_string: Query results or error message
                - is_error: True if an error occurred, False otherwise
        """
        if not self.connection or not self.cursor:
            return "Error: Database not initialized", True
        
        # Strip and validate query
        query = query.strip()
        if not query:
            return "Error: Empty query provided", True
        
        # MUTATION BLOCKER: Check for destructive operations
        mutation_error = self.check_mutation(query)
        if mutation_error:
            return mutation_error, True
        
        try:
            # Execute with timeout protection
            with timeout_handler(QUERY_TIMEOUT):
                self.cursor.execute(query)
                
                # OOM PROTECTION: Use fetchmany(50), NEVER fetchall()
                rows = self.cursor.fetchmany(MAX_FETCH_ROWS)
                
                if not rows:
                    # Check if it was a query that doesn't return rows
                    if self.cursor.description is None:
                        return "Query executed successfully (no results)", False
                    return "Query returned no results", False
                
                # Get column names
                columns = [desc[0] for desc in self.cursor.description]
                
                # Format results
                result_lines = []
                result_lines.append("| " + " | ".join(columns) + " |")
                result_lines.append("|" + "|".join(["---"] * len(columns)) + "|")
                
                for row in rows:
                    formatted_row = [str(val) if val is not None else "NULL" for val in row]
                    result_lines.append("| " + " | ".join(formatted_row) + " |")
                
                result = "\n".join(result_lines)
                
                # Check if results were truncated
                # Try to fetch one more row to see if there are more
                extra = self.cursor.fetchmany(1)
                if extra:
                    result += f"\n\n[TRUNCATED] Results limited to {MAX_FETCH_ROWS} rows. More rows exist."
                
                return result, False
                
        except TimeoutError as e:
            return f"Error: {str(e)}", True
        except sqlite3.Error as e:
            return f"SQLite Error: {str(e)}", True
        except Exception as e:
            return f"Error: {str(e)}", True
    
    def close(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None
        self._schema_cache = None
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()
