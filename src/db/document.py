from typing import Any, List, Optional

from psycopg import AsyncConnection
from pydantic.types import UUID4

from src.lib.logger import logger
from src.schemas.models.document import SQLDocument


async def get_document_by_name(
    doc_name: str, db_conn: AsyncConnection
) -> dict[str, Any] | None:
    """Retrieve a document from the database by its name.

    Args:
        doc_name: The unique name of the document to retrieve.
        db_conn: Database connection instance.

    Returns:
        Dictionary containing document data if found, None if no document exists.

    Raises:
        ValueError: If an error occurs during database operation.
    """
    try:
        # Check if the document exists in the database
        query = "SELECT * FROM document WHERE name = %s"
        cur = await db_conn.execute(
            query=query,
            params=(doc_name,),
        )

        result = await cur.fetchone()

        doc = result if result else None
        if not doc:
            return None

        return doc

    except Exception as e:
        logger.error(
            f"Error in `get_document_by_name`: Exception encountered while retrieving document '{doc_name}'. Error: {e}"
        )
        raise ValueError(f"Error retrieving document: {e}")


async def get_document_by_id(
    doc_id: UUID4, db_conn: AsyncConnection
) -> SQLDocument | None:
    """Retrieve a document from the database by its id.

    Args:
        doc_id: The unique ID of the document to retrieve.
        db_conn: Database connection instance.

    Returns:
        SQLDocument containing document data if found, None if no document exists.

    Raises:
        ValueError: If an error occurs during database operation.

    """
    try:
        # Check if the document exists in the database
        query = "SELECT * FROM document WHERE id = %s"
        cur = await db_conn.execute(
            query=query,
            params=(doc_id,),
        )

        result = await cur.fetchone()

        doc = result if result else None

        if not doc:
            return None

        return SQLDocument(**doc)

    except Exception as e:
        logger.error(
            f"Error in `get_document_by_id`: Exception encountered while retrieving document '{doc_id}'. Error: {e}"
        )
        raise ValueError(f"Error retrieving document: {e}")


async def get_document_id_by_name(
    db_conn: AsyncConnection,
    document_name: str,
) -> Optional[UUID4]:
    """
    Get document ID from the database by document name.

    Args:
        db: Database handler instance
        document_name: Name of the document

    Returns:
        UUID of the document if found, None otherwise
    """
    try:
        query = "SELECT id FROM document WHERE name = %s"
        parameters = (document_name,)

        cur = await db_conn.execute(
            query=query,
            params=parameters,
        )

        result = await cur.fetchone()

        if not result:
            logger.warning(f"Document with name '{document_name}' not found")
            return None

        return result["id"]
    except Exception as e:
        logger.error(f"Error retrieving document ID: {e}")
        raise ValueError(f"Error retrieving document: {e}")


async def get_documents(
    db_conn: AsyncConnection,
) -> List[SQLDocument]:
    """Retrieve all documents from the database.

    Args:
        db_conn: Database connection instance.

    Returns:
        List of SQLDocument containing document data. Empty list if no documents exist.

    Raises:
        ValueError: If an error occurs during database operation.
    """
    try:
        # Fetch all documents from the database
        query = "SELECT * FROM document"
        cur = await db_conn.execute(
            query=query,
        )

        result = await cur.fetchall()

        if not result:
            logger.info("No documents found in the database")
            return []

        return [SQLDocument(**doc) for doc in result]
    except Exception as e:
        logger.error(
            f"Error in `get_documents`: Exception encountered while retrieving documents. Error: {e}",
            exc_info=True,
        )
        raise ValueError(f"Error retrieving documents: {e}")
