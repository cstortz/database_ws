import re
import logging
from typing import List, Set, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SQLSecurity:
    """SQL Injection Protection and Validation"""
    
    # Dangerous SQL keywords that should be blocked
    DANGEROUS_KEYWORDS = {
        'DROP', 'TRUNCATE', 'ALTER', 'CREATE',
        'EXEC', 'EXECUTE', 'EXECUTE IMMEDIATE', 'EXECUTE PROCEDURE',
        'UNION', 'UNION ALL', 'SELECT INTO', 'COPY',
        'GRANT', 'REVOKE', 'DENY', 'BACKUP', 'RESTORE',
        'SHUTDOWN', 'KILL', 'RECONFIGURE', 'RECOVERY',
        'BULK INSERT', 'OPENROWSET', 'OPENDATASOURCE',
        'xp_', 'sp_', 'sys.', 'pg_', 'pg_catalog.'
    }
    
    # Allowed SQL keywords for raw queries (read-only operations)
    ALLOWED_READ_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'ORDER BY', 'GROUP BY', 'HAVING',
        'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN',
        'CROSS JOIN', 'FULL JOIN', 'NATURAL JOIN',
        'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'ILIKE',
        'IS NULL', 'IS NOT NULL', 'DISTINCT', 'TOP', 'LIMIT', 'OFFSET',
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COALESCE', 'NULLIF',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'AS', 'ASC', 'DESC', 'ASCENDING', 'DESCENDING'
    }
    
    # Allowed SQL keywords for write operations
    ALLOWED_WRITE_KEYWORDS = {
        'INSERT', 'UPDATE', 'DELETE', 'VALUES', 'SET',
        'RETURNING', 'ON CONFLICT', 'ON DUPLICATE KEY UPDATE',
        'MERGE', 'UPSERT', 'CREATE TEMP TABLE', 'CREATE TEMPORARY TABLE',
        'IF NOT EXISTS', 'CAST'
    }
    
    def __init__(self):
        self.blocked_patterns = self._compile_blocked_patterns()
    
    def _compile_blocked_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for blocked SQL patterns"""
        patterns = [
            # Block multiple statements
            r';\s*[A-Z]',
            # Block comments that could hide malicious code
            r'/\*.*?\*/',
            r'--.*$',
            # Block common injection patterns
            r'(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+',
            r'(\bOR\b|\bAND\b)\s+\'[^\']*\'',
            r'(\bOR\b|\bAND\b)\s+\"[^\"]*\"',
            # Block UNION attacks
            r'UNION\s+ALL?\s+SELECT',
            # Block stacked queries
            r';\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER)',
            # Block system table access
            #r'\b(sys\.|information_schema\.|pg_|pg_catalog\.)\w+',
            # Block stored procedure execution
            r'\b(EXEC|EXECUTE|CALL)\b',
            # Block file operations
            r'\b(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b',
            # Block dangerous functions
            r'\b(xp_|sp_)\w+',
        ]
        return [re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL) for pattern in patterns]
    
    def validate_sql_statement(self, sql: str, operation_type: str = "read") -> bool:
        """
        Validate SQL statement for injection attempts
        
        Args:
            sql: SQL statement to validate
            operation_type: "read" or "write" to determine allowed keywords
            
        Returns:
            bool: True if valid, False if injection detected
            
        Raises:
            HTTPException: If SQL injection is detected
        """
        if not sql or not sql.strip():
            raise HTTPException(status_code=400, detail="Empty SQL statement")
        
        # Convert to uppercase for keyword checking
        sql_upper = sql.upper().strip()
        
        # Check for dangerous keywords (with exceptions for write operations)
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in sql_upper:
                # Allow CREATE TEMP TABLE for write operations
                if keyword == 'CREATE' and operation_type == "write" and 'CREATE TEMP TABLE' in sql_upper:
                    continue
                logger.warning(f"SQL injection attempt detected: dangerous keyword '{keyword}'")
                raise HTTPException(
                    status_code=400, 
                    detail=f"SQL injection attempt detected: dangerous keyword '{keyword}'"
                )
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if pattern.search(sql):
                logger.warning(f"SQL injection attempt detected: blocked pattern '{pattern.pattern}'")
                raise HTTPException(
                    status_code=400,
                    detail="SQL injection attempt detected: blocked pattern"
                )
        
        # Validate based on operation type
        if operation_type == "read":
            return self._validate_read_operation(sql_upper)
        elif operation_type == "write":
            return self._validate_write_operation(sql_upper)
        else:
            raise HTTPException(status_code=400, detail="Invalid operation type")
    
    def _validate_read_operation(self, sql_upper: str) -> bool:
        """Validate read-only SQL operations"""
        # Must start with SELECT
        if not sql_upper.startswith('SELECT'):
            raise HTTPException(
                status_code=400,
                detail="Read operations must start with SELECT"
            )
        
        # Check for any write keywords
        for keyword in self.ALLOWED_WRITE_KEYWORDS:
            if keyword in sql_upper:
                logger.warning(f"Write operation detected in read query: '{keyword}'")
                raise HTTPException(
                    status_code=400,
                    detail=f"Write operations not allowed in read queries: '{keyword}'"
                )
        
        return True
    
    def _validate_write_operation(self, sql_upper: str) -> bool:
        """Validate write SQL operations"""
        # Must start with INSERT, UPDATE, DELETE, or CREATE TEMP TABLE
        valid_starts = ['INSERT', 'UPDATE', 'DELETE', 'CREATE TEMP TABLE', 'CREATE TEMPORARY TABLE', 'CREATE TEMP TABLE IF NOT EXISTS']
        if not any(sql_upper.startswith(start) for start in valid_starts):
            raise HTTPException(
                status_code=400,
                detail="Write operations must start with INSERT, UPDATE, DELETE, or CREATE TEMP TABLE"
            )
        
        return True
    
    def sanitize_identifier(self, identifier: str) -> str:
        """
        Sanitize SQL identifier (table name, column name, etc.)
        
        Args:
            identifier: Identifier to sanitize
            
        Returns:
            str: Sanitized identifier
        """
        if not identifier:
            raise HTTPException(status_code=400, detail="Empty identifier")
        
        # Remove any SQL injection attempts
        dangerous_chars = [';', '--', '/*', '*/', "'", '"', '`']
        for char in dangerous_chars:
            if char in identifier:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid character in identifier: '{char}'"
                )
        
        # Only allow alphanumeric, underscore, and dot
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$', identifier):
            raise HTTPException(
                status_code=400,
                detail="Invalid identifier format"
            )
        
        return identifier
    
    def validate_table_name(self, table_name: str) -> str:
        """
        Validate and sanitize table name
        
        Args:
            table_name: Table name to validate
            
        Returns:
            str: Sanitized table name
        """
        return self.sanitize_identifier(table_name)
    
    def validate_schema_name(self, schema_name: str) -> str:
        """
        Validate and sanitize schema name
        
        Args:
            schema_name: Schema name to validate
            
        Returns:
            str: Sanitized schema name
        """
        return self.sanitize_identifier(schema_name)

# Global instance
sql_security = SQLSecurity() 