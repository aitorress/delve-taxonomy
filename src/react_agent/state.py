"""Define the state structures for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated, List, Optional, Dict, Sequence
import operator

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep


@dataclass
class Doc:
    """Represents a document in the taxonomy generation process."""
    id: str
    content: str
    summary: Optional[str] = None
    explanation: Optional[str] = None
    category: Optional[str] = None


@dataclass
class InputState:
    """Defines the input state for the agent, representing initial configuration parameters.
    
    This class contains only the essential input parameters needed to initialize the taxonomy generation process.
    """
    project_name: str
    days: int
    org_id: str
    messages: Annotated[Sequence[AnyMessage], add_messages] = field(default_factory=list)


@dataclass
class State(InputState):
    """Represents the complete state of the taxonomy generation agent.
    
    This class extends InputState with additional attributes needed throughout the taxonomy generation process.
    """
    all_documents: List[Doc] = field(default_factory=list)
    documents: List[Doc] = field(default_factory=list)
    minibatches: List[List[int]] = field(default_factory=list)
    clusters: Annotated[List[List[Dict]], operator.add] = field(default_factory=list)
    status: Annotated[List[str], operator.add] = field(default_factory=list)
    use_case: str = field(default="")
    is_last_step: IsLastStep = field(default=False)
