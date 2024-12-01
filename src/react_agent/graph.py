"""Define the taxonomy generation graph structure."""

from typing import Literal
from langgraph.graph import StateGraph

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.nodes.runs_retriever import retrieve_runs
from react_agent.nodes.summary_generator import generate_summaries
from react_agent.nodes.minibatches_generator import generate_minibatches
from react_agent.nodes.taxonomy_generator import generate_taxonomy
from react_agent.nodes.taxonomy_updater import update_taxonomy
from react_agent.nodes.taxonomy_reviewer import review_taxonomy


# Create the graph
builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Add nodes
builder.add_node("get_runs", retrieve_runs)
builder.add_node("summarize", generate_summaries)
builder.add_node("get_minibatches", generate_minibatches)
builder.add_node("generate_taxonomy", generate_taxonomy)
builder.add_node("update_taxonomy", update_taxonomy)
builder.add_node("review_taxonomy", review_taxonomy)

# Define the review decision function
def should_review(state: State) -> Literal["update_taxonomy", "review_taxonomy"]:
    """Determine whether to continue updating or move to review.
    
    Args:
        state (State): The current state of the taxonomy generation process.
    
    Returns:
        str: Either "update_taxonomy" or "review_taxonomy" based on progress.
    """
    num_minibatches = len(state.minibatches)
    num_revisions = len(state.clusters)
    if num_revisions < num_minibatches:
        return "update_taxonomy"
    return "review_taxonomy"

# Add edges
builder.add_edge("__start__", "get_runs")
builder.add_edge("get_runs", "summarize")
builder.add_edge("summarize", "get_minibatches")
builder.add_edge("get_minibatches", "generate_taxonomy")
builder.add_edge("generate_taxonomy", "update_taxonomy")

# Add conditional edges for the review process
builder.add_conditional_edges(
    "update_taxonomy",
    should_review,
    {
        "update_taxonomy": "update_taxonomy",
        "review_taxonomy": "review_taxonomy"
    }
)

builder.add_edge("review_taxonomy", "__end__")

# Compile the graph
graph = builder.compile()
graph.name = "Taxonomy Generation"  # Add a name for LangSmith tracking
