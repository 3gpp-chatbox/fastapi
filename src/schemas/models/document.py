"""Pydantic models for document processing."""

from datetime import datetime

from pydantic import BaseModel, Field
from pydantic.types import UUID4


class BaseDocument(BaseModel):
    """Core 3GPP document metadata.

    Attributes:
        spec: 3GPP specification number (e.g., "38.331")
        version: Document version identifier
        release: 3GPP release number (e.g., 15, 16, 17)
    """

    spec: str = Field(description="3GPP specification number (e.g., '38.331')")
    version: str = Field(description="Document version identifier")
    release: int = Field(description="3GPP release number (e.g., 15, 16, 17)")


class SQLDocument(BaseDocument):
    """Stored 3GPP document in database.

    Attributes:
        id: UUID primary key for the document
        spec: 3GPP specification number (e.g., "38.331")
        release: 3GPP release version (e.g., "Rel-15")
        toc: Table of contents in markdown format for quick navigation
        extracted_at: ISO format timestamp of document extraction
    """

    id: UUID4 = Field(description="UUID primary key for the document")
    toc: str = Field(
        description="Table of contents in markdown format for quick navigation"
    )
    extracted_at: datetime = Field(
        description="Timestamp of when the document was extracted"
    )
