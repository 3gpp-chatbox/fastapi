from typing import AsyncGenerator

from fastapi import Request
from psycopg import AsyncConnection

from src.db.db_ahandler import AsyncDatabaseHandler


# Dependency to get a database connection per request
async def get_db_connection(request: Request) -> AsyncGenerator[AsyncConnection, None]:
    db_handler: AsyncDatabaseHandler = request.app.state.db_handler
    async with db_handler.get_connection() as conn:
        yield conn
