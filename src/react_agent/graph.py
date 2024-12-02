"""Define the taxonomy generation graph structure."""

from typing import Literal
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from react_agent.configuration import Configuration
from react_agent.state import InputState, State, UserFeedback
from react_agent.nodes.runs_retriever import retrieve_runs
from react_agent.nodes.summary_generator import generate_summaries
from react_agent.nodes.minibatches_generator import generate_minibatches
from react_agent.nodes.taxonomy_generator import generate_taxonomy
from react_agent.nodes.taxonomy_updater import update_taxonomy
from react_agent.nodes.taxonomy_reviewer import review_taxonomy
from react_agent.nodes.taxonomy_approval import request_taxonomy_approval
from langchain_core.runnables import RunnableConfig
from react_agent.nodes.doc_labeler import label_documents
from react_agent.utils import load_chat_model
from react_agent.prompts import FEEDBACK_PROMPT  


async def confirmed(state: State, config: RunnableConfig) -> dict:
    """Acknowledge the approval of taxonomy clusters."""
    message = AIMessage(content="✅ Taxonomy clusters have been approved. Thank you for your confirmation!")
    print("\nTaxonomy confirmed and finalized.")
    return {"messages": [message], "status": ["Taxonomy approved"]}

# Create the graph
builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Add nodes
builder.add_node("get_runs", retrieve_runs)
builder.add_node("summarize", generate_summaries)
builder.add_node("get_minibatches", generate_minibatches)
builder.add_node("generate_taxonomy", generate_taxonomy)
builder.add_node("update_taxonomy", update_taxonomy)
builder.add_node("review_taxonomy", review_taxonomy)
builder.add_node("approve_taxonomy", request_taxonomy_approval)
builder.add_node("label_documents", label_documents)

# Define the review decision function
def should_review(state: State) -> Literal["update_taxonomy", "review_taxonomy"]:
    """Determine whether to continue updating or move to review."""
    num_minibatches = len(state.minibatches)
    num_revisions = len(state.clusters)
    if num_revisions < num_minibatches:
        return "update_taxonomy"
    return "review_taxonomy"


async def handle_user_feedback(state: State, config: RunnableConfig) -> Literal["continue", "modify"]:
    configuration = Configuration.from_runnable_config(config)

    # Initialize the fast LLM for outline generation
    model = load_chat_model(configuration.model)

    # Get the topic from the last user message
    last_user_message = next(
        (msg for msg in reversed(state.messages) if msg.type == "human"),
        None,
    )
    if not last_user_message:
        raise ValueError("No user message found in state")

    # Create the chain for outline generation with structured output
    chain = FEEDBACK_PROMPT | model.with_structured_output(UserFeedback)

    result = await chain.ainvoke({"input": last_user_message.content}, config)


    print(f"User feedback: {result}")
    return result["decision"]

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

# Add final approval step with feedback handling
builder.add_edge("review_taxonomy", "approve_taxonomy")
builder.add_conditional_edges(
    "approve_taxonomy",
    handle_user_feedback,
    {
        "continue": "label_documents",
        "modify": "generate_taxonomy"
    }
)

# Add final edges
builder.add_edge("label_documents", "__end__")

memory = MemorySaver()

# Compile the graph with breakpoints for approval
graph = builder.compile(
    checkpointer=memory,
    interrupt_after=["approve_taxonomy"]
)
graph.name = "Taxonomy Generation"
