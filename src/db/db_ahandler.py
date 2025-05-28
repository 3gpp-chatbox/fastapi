"""Database handler module for managing PostgreSQL database connections and operations.

This module provides a DatabaseHandler class that manages database connections,
transactions, and CRUD operations with proper resource management and error handling.
Uses connection pooling for efficient connection management and async operations
for better performance under load.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from psycopg import AsyncConnection, Error, OperationalError
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from src.lib.logger import logger


class AsyncDatabaseHandler:
    """A class to handle PostgreSQL database operations with async connection pooling.

    This class manages a pool of database connections using async/await patterns,
    providing efficient connection management and automatic cleanup through context managers.
    It handles connection lifecycle, pooling, and error management automatically.

    Usage:
        ```python
        async with AsyncDatabaseHandler() as db:
            async with db.get_connection() as conn:
                # Simple query
                results = await conn.execute("SELECT * FROM table").fetchall()

                # Transaction management
                async with conn.transaction():
                    await conn.execute("INSERT INTO table VALUES (%s)", ("data",))
        ```

    Attributes:
        pool (AsyncConnectionPool): The connection pool for managing connections.
        dbname (str): Database name from DB_NAME environment variable.
        host (str): Database host address from DB_HOST environment variable.
        user (str): Database user from DB_USER environment variable.
        password (str): Database password from DB_PASSWORD environment variable.
        port (str): Database port from DB_PORT environment variable.
        min_size (int): Minimum number of connections in the pool.
        max_size (int): Maximum number of connections in the pool.
    """

    def __init__(self, min_size: int = 3, max_size: int = 10) -> None:
        """Initialize the DatabaseHandler with connection parameters from environment variables.

        Args:
            min_size (int, optional): Minimum number of connections in the pool. Defaults to 3.
            max_size (int, optional): Maximum number of connections in the pool. Defaults to 10.

        Raises:
            ValueError: If any required environment variables are missing.
        """
        self.dbname: str = os.getenv("DB_NAME", "")
        self.host: str = os.getenv("DB_HOST", "")
        self.user: str = os.getenv("DB_USER", "")
        self.password: str = os.getenv("DB_PASSWORD", "")
        self.port: str = os.getenv("DB_PORT", "")

        if not all([self.dbname, self.host, self.user, self.password, self.port]):
            raise ValueError("Missing required database configuration")

        self.pool: Optional[AsyncConnectionPool] = None
        self.min_size = min_size
        self.max_size = max_size

    async def __aenter__(self) -> "AsyncDatabaseHandler":
        """Enter async context manager and establish connection pool.

        Returns:
            AsyncDatabaseHandler: Self reference for context management.
        """
        await self._connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager and cleanup resources."""
        await self._disconnect()

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[AsyncConnection, None]:
        """Get a pooled database connection using async context management.

        This method provides a connection from the pool that can be used for database
        operations. The connection is automatically returned to the pool when the
        context is exited. Transactions can be managed explicitly using the connection's
        transaction() context manager.

        Usage:
            ```python
            async with db.get_connection() as conn:
                # Direct query execution
                results = await conn.execute("SELECT * FROM table").fetchall()

                # Explicit transaction
                async with conn.transaction():
                    await conn.execute("INSERT INTO table VALUES (%s)", ("data",))
            ```

        Yields:
            AsyncConnection: A connection from the pool with transaction support.

        Raises:
            OperationalError: If connection issues occur.
        """
        if not self.pool:
            await self._connect()

        async with self.pool.connection() as conn:
            await conn.set_autocommit(True)
            try:
                yield conn
            except Error as e:
                logger.error(f"Error while using connection: {str(e)}")
                raise

    def _get_connection_string(self) -> str:
        """Generate the connection string from instance attributes.

        Returns:
            str: Formatted connection string for database connection.
        """
        return (
            f"host={self.host} "
            f"dbname={self.dbname} "
            f"user={self.user} "
            f"password={self.password} "
            f"port={self.port}"
        )

    async def _connect(self) -> None:
        """Establish the connection pool.

        Raises:
            OperationalError: If pool cannot be established.
            ValueError: If required configuration is missing.
        """
        try:
            if not self.pool:
                logger.info("Establishing connection pool...")
                self.pool = AsyncConnectionPool(
                    open=False,
                    conninfo=self._get_connection_string(),
                    min_size=self.min_size,
                    max_size=self.max_size,
                    kwargs={"row_factory": dict_row},
                )
                await self.pool.open()
                logger.info("Connection pool established successfully")
        except Exception as e:
            logger.error(f"Failed to establish connection pool: {str(e)}")
            raise OperationalError(f"Connection pool creation failed: {str(e)}")

    async def _disconnect(self) -> None:
        """Close the connection pool if it exists."""
        if self.pool:
            logger.info("Closing connection pool...")
            await self.pool.close()
            self.pool = None
            logger.info("Connection pool closed")
