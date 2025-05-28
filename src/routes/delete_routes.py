from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection

from src.dependecies import get_db_connection
from src.lib.logger import logger

router = APIRouter()


@router.delete("/{procedure_id}/{entity}")
async def delete_procedure_graph(
    procedure_id: UUID,
    entity: str,
    conn: Annotated[AsyncConnection, Depends(get_db_connection)],
):
    """
    Delete all graphs for a specific procedure and entity combination.
    If no graphs remain for the procedure after deletion, the procedure itself will also be deleted.

    Args:
        procedure_id (UUID): The UUID of the procedure
        entity (str): The entity type (e.g., 'UE', 'AMF')
        conn: Database connection from dependency injection

    Returns:
        dict: A message indicating successful deletion and whether the procedure was also deleted

    Raises:
        HTTPException: If the procedure/entity combination doesn't exist or deletion fails
    """
    try:
        async with conn.transaction():
            # First check if procedure and entity combination exists
            query = """
            SELECT p.name as procedure_name, COUNT(g.id) as graph_count
            FROM procedure p
            JOIN graph g ON p.id = g.procedure_id
            WHERE p.id = %s AND LOWER(g.entity) = LOWER(%s)
            GROUP BY p.name
            """
            result = await conn.execute(query, (procedure_id, entity))
            procedure_info = await result.fetchone()

            if not procedure_info:
                raise HTTPException(
                    status_code=404,
                    detail=f"No graphs found for procedure {procedure_id} and entity {entity}",
                )

            # Delete all graphs for this procedure and entity
            delete_query = """
            DELETE FROM graph 
            WHERE procedure_id = %s AND LOWER(entity) = LOWER(%s)
            """
            await conn.execute(delete_query, (procedure_id, entity))

            # Check if any graphs remain for this procedure
            remaining_graphs_query = """
            SELECT COUNT(*) as remaining_count
            FROM graph
            WHERE procedure_id = %s
            """
            result = await conn.execute(remaining_graphs_query, (procedure_id,))
            remaining_count = await result.fetchone()

            procedure_deleted = False
            if remaining_count["remaining_count"] == 0:
                # No graphs remain, delete the procedure
                delete_procedure_query = """
                DELETE FROM procedure
                WHERE id = %s
                """
                await conn.execute(delete_procedure_query, (procedure_id,))
                procedure_deleted = True

            return {
                "message": f"Successfully deleted {procedure_info['graph_count']} graphs for procedure '{procedure_info['procedure_name']}' ({entity} side)",
                "procedure_deleted": procedure_deleted,
                "procedure_name": procedure_info["procedure_name"],
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete procedure graphs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete procedure graphs")
