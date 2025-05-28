from psycopg import AsyncConnection
from pydantic.types import UUID4

from src.db.document import get_document_by_id
from src.lib.generate_markdown import generate_markdown
from src.lib.logger import logger


async def get_sections_content(
    db_conn: AsyncConnection, doc_id: UUID4, section_list: list[str]
) -> str:
    """Fetch and format section contents from a document based on section identifiers.
    Args:
        db_conn (AsyncConnection): Database connection instance.
        doc_id (UUID4): ID of the document to fetch sections from.
        section_list (list[str]): List of section identifiers to fetch.

    Returns:
        str: Markdown formatted string containing the fetched sections

    Raises:
        ValueError: If document is not found or sections cannot be retrieved.
        Exception: For any other database or processing errors.
    """
    if not doc_id:
        raise ValueError("Missing required argument: doc_id")
    if not section_list:
        raise ValueError("Missing required argument: section_list")
    if not all(isinstance(section, str) for section in section_list):
        raise ValueError("All section identifiers must be strings")

    try:
        async with db_conn.cursor() as cur:
            document = await get_document_by_id(doc_id=doc_id, db_conn=db_conn)

            if not document:
                raise ValueError(
                    f"Document with ID '{doc_id}' not found in the database."
                )

            # Step 2: Fetch the path for every section in the section_list
            # Find all sections whose headings match the given patterns
            # Uses ILIKE for case-insensitive matching and checks if section heading starts with pattern
            path_fetch_query = """
            SELECT 
                heading,
                path
            FROM section 
            WHERE document_id = %s
                AND EXISTS (
                    SELECT 1 
                    FROM unnest(%s::text[]) AS pattern
                    WHERE section.heading ILIKE pattern || ' %%'
                )
            """

            await cur.execute(
                query=path_fetch_query,
                params=(document.id, section_list),
            )

            sections = await cur.fetchall()

            if not sections:
                raise ValueError(
                    f"No sections found for document '{document.spec} {document.version}' with the given parameter: {section_list}"
                )

            logger.info(
                f"Found {len(sections)} matching sections for document '{document.spec} {document.version}'"
            )

            sections_path = [section["path"] for section in sections]
            sections_heading = [section["heading"] for section in sections]

            logger.debug(
                f"Matched sections for document '{document.spec} {document.version}': {', '.join(sections_heading)}"
            )

            # Step 3: Fetch the contents for every section hirearchaly in the sections_path
            # Fetch content for all sections hierarchically using ltree path operator
            # path <@ ANY (%s) finds all sections whose path is descendant of any given path
            content_fetch_query = """
            SELECT 
                heading,
                level,
                content
            FROM section
            WHERE document_id = %s
                AND path <@ ANY (%s)
            ORDER BY path
            """

            await cur.execute(
                query=content_fetch_query,
                params=(document.id, sections_path),
            )

            sections_content = await cur.fetchall()

            if not sections_content:
                raise ValueError(
                    f"Failed to perform hierarchical search for document '{document.spec} {document.version}' with the given parameter: {section_list}"
                )

            logger.debug(
                f"Retrieved {len(sections_content)} sections (including subsections) "
                f"for document '{document.spec} {document.version}' under paths: {', '.join(sections_path)}"
            )

            # Step 4 generate markdown
            markdown = generate_markdown(document.spec, sections_content)

            return markdown

    except Exception as e:
        logger.error("Error in `fetch_sections_content`", exc_info=True)
        raise Exception(
            f"fetch_sections_content: Failed to retrieve sections: {str(e)}"
        ) from e
