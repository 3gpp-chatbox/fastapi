from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection

from src.db.sections_content_retrieval import get_sections_content
from src.dependecies import get_db_connection
from src.lib.logger import logger
from src.schemas.models.models import NewGraphInsert, ProcedureItem, Reference

router = APIRouter()


@router.post("/{procedure_id}/{entity}", response_model=ProcedureItem)
async def insert_edited_graph(
    procedure_id: UUID,
    entity: str,
    request: NewGraphInsert,
    conn: Annotated[AsyncConnection, Depends(get_db_connection)],
):
    """
    Insert a new graph version with user-edited extracted data.

    Args:
        procedure_id: UUID of the procedure
        entity: Entity type (e.g., 'UE', 'AMF')
        request: Contains the edited `extracted_data` and commit info
        conn: Database connection from dependency injection

    Returns:
        NewProcedureItemInfo: Newly inserted graph row
    """
    try:
        async with conn.cursor() as cur:
            # Get procedure and document info
            proc_query = """
            SELECT p.name, p.retrieved_top_sections, p.extracted_at, d.id AS document_id, d.spec AS document_spec,
                d.version AS document_version, d.release AS document_release
            FROM procedure p
            JOIN document d ON p.document_id = d.id
            WHERE p.id = %s 
            """
            await cur.execute(
                query=proc_query,
                params=(procedure_id,),
            )

            proc = await cur.fetchone()

            if not proc:
                raise HTTPException(status_code=404, detail="Procedure not found")

            # Get latest graph for metadata reuse
            latest_query = """
            SELECT model_name, accuracy, extraction_method, COALESCE(MAX(version::int), 0) as latest_version
            FROM graph
            WHERE procedure_id = %s AND LOWER(entity) = LOWER(%s)
            GROUP BY model_name, accuracy, extraction_method
            ORDER BY latest_version DESC
            LIMIT 1
            """
            await cur.execute(
                query=latest_query,
                params=(procedure_id, entity),
            )

            latest_result = await cur.fetchone()

            if not latest_result:
                raise HTTPException(status_code=404, detail="Graph not found")

            latest = latest_result
            next_version = str(int(latest["latest_version"]) + 1)
            status = "verified"

            # Serialize edited graph to JSON string
            edited_graph_json = request.edited_graph.model_dump_json(by_alias=True)

            insert_query = """
            INSERT INTO graph (
                entity, extracted_data, model_name, accuracy,
                status, extraction_method, commit_title, commit_message,
                version, procedure_id
            ) VALUES (%s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            """
            insert_params = (
                entity.upper(),
                edited_graph_json,
                latest["model_name"],
                latest["accuracy"],
                status,
                latest["extraction_method"],
                request.commit_title,
                request.commit_message,
                next_version,
                procedure_id,
            )

            await cur.execute(
                query=insert_query,
                params=insert_params,
            )

            insert_result = await cur.fetchone()

            if not insert_result:
                raise HTTPException(
                    status_code=500, detail="Failed to insert edited graph"
                )

            new_graph = insert_result

            context_md = await get_sections_content(
                db_conn=conn,
                doc_id=proc["document_id"],
                section_list=proc["retrieved_top_sections"],
            )

            return ProcedureItem(
                document_id=proc["document_id"],
                document_spec=proc["document_spec"],
                document_version=proc["document_version"],
                document_release=proc["document_release"],
                procedure_id=procedure_id,
                procedure_name=proc["name"],
                extracted_at=proc["extracted_at"],
                reference=Reference(context_markdown=context_md),
                graph_id=new_graph["id"],
                entity=entity,
                graph=request.edited_graph,
                accuracy=latest["accuracy"],
                created_at=new_graph["created_at"],
                extraction_method=latest[
                    "extraction_method"
                ],  # reused, not overridden with 'modified'
                model_name=latest["model_name"],
                version=next_version,
                status=status,
                commit_title=request.commit_title,
                commit_message=request.commit_message,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to insert edited graph: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to insert edited graph")
