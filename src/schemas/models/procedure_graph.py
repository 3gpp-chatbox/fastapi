# schema_validation.py
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class BaseNode(BaseModel):
    """Base node definition containing core node attributes."""

    id: str = Field(
        ...,
        description="Unique identifier for the node",
    )

    type: Literal["state", "event"] = Field(
        ..., description="Type of the node, either 'state' or 'event'."
    )

    section_reference: str = Field(
        ...,
        description="The immediate section from which the node is referenced (eg., 4.2.1 Section Name)",
    )

    text_reference: str = Field(
        ...,
        description="The exact text from the context that was used to create the node",
    )


class BaseEdge(BaseModel):
    """Base edge definition for connections between nodes."""

    from_node: str = Field(
        ...,
        alias="from",
        description="ID of the starting node.",
    )

    to: str = Field(
        ...,
        description="ID of the target node.",
    )

    type: str = Field(
        ..., description="Type of the edge, either 'trigger' or 'condition'."
    )

    section_reference: str = Field(
        ...,
        description="The immediate section from which the edge is referenced (eg., 4.2.1 Section Name)",
    )

    text_reference: str = Field(
        ...,
        description="The exact text from the context that was used to create the edge",
    )

    model_config = ConfigDict(serialize_by_alias=True)


class Node(BaseNode):
    """Node with additional description field."""

    description: str = Field(
        ...,
        description="Explanation of the state or event.",
    )

    # model_config = ConfigDict(extra="forbid")


class Edge(BaseEdge):
    """Edge with additional description field."""

    description: str = Field(
        ..., description="Explanation of the trigger or condition."
    )

    model_config = ConfigDict(serialize_by_alias=True)


class BaseGraph(BaseModel):
    """Initial graph structure from first extraction step."""

    nodes: List[BaseNode] = Field(
        ...,
        description="List of all states and events.",
    )

    edges: List[BaseEdge] = Field(
        ..., description="List of all triggers and conditions."
    )


class Graph(BaseModel):
    """Complete procedure graph with enriched nodes and edges."""

    nodes: List[Node] = Field(..., description="List of all states and events.")
    edges: List[Edge] = Field(..., description="List of all triggers and conditions.")
