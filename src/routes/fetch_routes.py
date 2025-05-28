from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection

from src.db.sections_content_retrieval import get_sections_content
from src.dependecies import get_db_connection
from src.lib.logger import logger
from src.schemas.models.models import (
    EntityVersionItem,
    OneHistoryVersionItem,
    ProcedureItem,
    ProcedureListItem,
    ProceduresByDocument,
    Reference,
)

router = APIRouter()


@router.get("/", response_model=list[ProceduresByDocument])
async def get_procedure_names_and_entities(
    conn: Annotated[AsyncConnection, Depends(get_db_connection)],
):
    """
    Get distinct procedure names and entities grouped by document.
    Used to populate the dropdown list on the frontend.
    """
    try:
        query = """
        SELECT 
            d.id as document_id,
            d.spec as document_spec,
            d.version as document_version,
            d.release as document_release,
            p.id as procedure_id,
            p.name as procedure_name,
            array_agg(DISTINCT g.entity) as entities
        FROM document d
        JOIN procedure p ON d.id = p.document_id
        JOIN graph g ON p.id = g.procedure_id
        GROUP BY d.id, d.spec, d.version, d.release, p.id, p.name
        ORDER BY d.release, d.spec, d.version, p.name
        """
        cur = await conn.execute(query=query)
        results = await cur.fetchall()

        # Group procedures by document
        doc_map = {}
        for row in results:
            doc_key = (
                row["document_id"],
                row["document_spec"],
                row["document_version"],
                row["document_release"],
            )
            if doc_key not in doc_map:
                doc_map[doc_key] = []
            doc_map[doc_key].append(
                ProcedureListItem(
                    procedure_id=row["procedure_id"],
                    procedure_name=row["procedure_name"],
                    entity=row["entities"],
                )
            )
        response = []
        for (
            document_id,
            document_spec,
            document_version,
            document_release,
        ), procedures in doc_map.items():
            response.append(
                ProceduresByDocument(
                    document_id=document_id,
                    document_spec=document_spec,
                    document_version=document_version,
                    document_release=document_release,
                    document_procedures=procedures,
                )
            )
        return response

    except Exception as e:
        logger.error(f"Failed to fetch procedures: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching procedures"
        )


@router.get("/{procedure_id}/{entity}", response_model=ProcedureItem)
async def get_latest_graph_by_procedure_id_and_entity(
    procedure_id: UUID,
    entity: str,
    conn: Annotated[AsyncConnection, Depends(get_db_connection)],
):
    """
    Get full latest graph data and metadata by procedure id and entity.
    """
    try:
        query = """
        SELECT 
            g.id as graph_id, g.entity, g.extracted_data, g.model_name, g.accuracy, g.version,
            g.created_at, g.status, g.extraction_method, g.commit_title, g.commit_message, g.entity,
            p.name as procedure_name,p.id as procedure_id, p.retrieved_top_sections, p.extracted_at,
            d.id as document_id, d.spec as document_spec, d.version as document_version, d.release as document_release
        FROM graph g
        JOIN procedure p ON g.procedure_id = p.id
        JOIN document d ON p.document_id = d.id
        WHERE p.id = %s AND LOWER(g.entity) = LOWER(%s)
        ORDER BY g.version::int DESC
        Limit 1
        """

        cur = await conn.execute(
            query=query,
            params=(procedure_id, entity),
        )

        result = await cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Graph not found")

        document_id = result["document_id"]
        top_sections = result["retrieved_top_sections"]

        context_md = await get_sections_content(
            db_conn=conn,
            doc_id=document_id,
            section_list=top_sections,
        )

        return ProcedureItem(
            document_id=result["document_id"],
            document_spec=result["document_spec"],
            document_version=result["document_version"],
            document_release=result["document_release"],
            procedure_name=result["procedure_name"],
            procedure_id=procedure_id,
            extraction_method=result["extraction_method"],
            extracted_at=result["extracted_at"],
            graph_id=result["graph_id"],
            graph=result["extracted_data"],
            model_name=result["model_name"],
            accuracy=result["accuracy"],
            created_at=result["created_at"],
            entity=result["entity"],
            version=result["version"],
            status=result["status"],
            commit_title=result["commit_title"],
            commit_message=result["commit_message"],
            reference=Reference(context_markdown=context_md),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch graph: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching graph"
        )


@router.get("/{procedure_id}/{entity}/history", response_model=list[EntityVersionItem])
async def get_graph_versions(
    procedure_id: UUID,
    entity: str,
    conn: Annotated[AsyncConnection, Depends(get_db_connection)],
):
    """
    Get brief info of all versions of a graph for a specific procedure name and entity type.
    """
    try:
        query = """
        SELECT 
        g.id as graph_id, g.version, g.created_at,g.commit_title,g.commit_message,
        p.name as procedure_name
        FROM graph g
        JOIN procedure p ON g.procedure_id = p.id
        WHERE p.id = %s AND LOWER(g.entity) = LOWER(%s)
        ORDER BY g.version::int DESC
        """
        cur = await conn.execute(query=query, params=(procedure_id, entity))
        results = await cur.fetchall()

        version_history = [
            EntityVersionItem(
                graph_id=row["graph_id"],
                version=row["version"],
                created_at=row["created_at"],
                commit_title=row["commit_title"],
                commit_message=row["commit_message"],
            )
            for row in results
        ]

        if not version_history:
            raise HTTPException(status_code=404, detail="No version history found")

        return version_history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch graph version history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch version history")


@router.get(
    "/{procedure_id}/{entity}/history/{graph_id}",
    response_model=OneHistoryVersionItem,
)
async def get_one_graph_version_detail(
    procedure_id: UUID,
    entity: str,
    graph_id: UUID,
    conn: Annotated[AsyncConnection, Depends(get_db_connection)],
):
    """
    Get one graph version detail for a specific procedure name and entity type.
    """
    try:
        query = """
        SELECT 
        g.extracted_data
        FROM graph g
        WHERE g.procedure_id = %s AND LOWER(g.entity) = LOWER(%s) AND g.id = %s
        """
        cur = await conn.execute(query=query, params=(procedure_id, entity, graph_id))

        result = await cur.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Graph not found")

        graph = result["extracted_data"]

        return OneHistoryVersionItem(graph=graph)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch graph: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch graph")
