"""
Defines API response/request models.
"""

from datetime import datetime
from typing import Optional

from pydantic import UUID4, BaseModel

from src.schemas.models.procedure_graph import Graph


class ProcedureListItem(BaseModel):
    """Basic procedure information for list view.

    Attributes:
        id: UUID of the procedure
        name: Name of the procedure
    """

    procedure_id: UUID4
    procedure_name: str
    entity: list[str]


class BaseDocument(BaseModel):
    """Base document metadata.

    Attributes:
        document_id: UUID of the document.
        document_spec: Specification string of the document.
        document_version: Version string of the document.
        document_release: Release number of the document.
    """

    document_id: UUID4
    document_spec: str
    document_version: str
    document_release: int


class ProceduresByDocument(BaseDocument):
    """Document metadata with associated procedures.

    Attributes:
        document_id: UUID of the document.
        document_spec: Specification string of the document.
        document_version: Version string of the document.
        document_release: Release number of the document.
        document_procedures: List of associated procedures (may be empty).
    """

    document_procedures: list[ProcedureListItem] = []


class Reference(BaseModel):
    context_markdown: str


class ProcedureItem(BaseDocument):
    """Procedure graph with metadata and accuracy.

    Attributes:
        id: UUID of the graph
        name: Name of the procedure
        document_id: UUID of the source document
        document_name: Name of the source document
        graph: JSON representation of the procedure graph
        created_at: Timestamp of graph creation
        accuracy: Confidence score of the procedure
        extracted_at: Timestamp of procedure extraction
        extraction_method: Method used to extract the graph
        model_name: Name of the model used
        entity: Type of network entity (e.g., UE, AMF)
        version: Version of the graph
        status: Status of the graph (e.g., new, verified)

    """

    procedure_id: UUID4
    procedure_name: str
    accuracy: float
    extraction_method: str
    extracted_at: datetime
    model_name: str
    reference: Reference
    graph_id: UUID4
    graph: Graph
    entity: str
    status: str
    version: str
    commit_title: str
    commit_message: str
    created_at: datetime


class EntityVersionItem(BaseModel):
    """Represents a version of a graph for a specific network entity.

    Attributes:
        graph_id: UUID of the graph
        entity: Type of the entity (e.g., UE, AMF)
        version: Version string of the graph
        accuracy: Accuracy of the graph extraction
        model_name: Name of the model used
        created_at: Timestamp when the graph was created
        commit_title: Title of the associated commit
        commit_message: Description of the associated commit
    """

    graph_id: UUID4
    version: str
    created_at: datetime
    commit_title: Optional[str] = None
    commit_message: Optional[str] = None


class Graph(Graph):
    pass


class NewGraphInsert(BaseModel):
    edited_graph: Graph
    commit_title: str
    commit_message: str


class OneHistoryVersionItem(BaseModel):
    graph: Graph
