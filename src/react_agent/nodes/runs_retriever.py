"""Node for retrieving runs from LangSmith."""

from datetime import datetime, timedelta
from langsmith import Client, traceable
from langchain_core.runnables import RunnableConfig

from react_agent.state import State
from react_agent.utils import process_runs


@traceable
async def retrieve_runs(state: State, config: RunnableConfig) -> dict:
    """Retrieve and process runs from LangSmith.
    
    Args:
        state: Current application state
        config: Configuration for the run
        
    Returns:
        dict: Updated state fields with retrieved documents
        
    Raises:
        ValueError: If project_name is not set
    """
    print("Starting taxonomy test...")

    if not state.project_name:
        raise ValueError("project_name not set in state")

    print(f"Using project: {state.project_name}")
    client = Client(api_key=state.org_id)

    print(f"Fetching runs from the past {state.days} days...")
    delta_days = datetime.now() - timedelta(days=state.days)

    max_runs = config["configurable"].get("max_runs", 500)
    print(f"Max runs set to: {max_runs}")

    runs = list(
        client.list_runs(
            project_name=state.project_name,
            filter="eq(is_root, true)",
            start_time=delta_days,
            select=["inputs", "outputs"],
            limit=max_runs,
        )
    )
    print(f"Fetched {len(runs)} runs.")

    if len(runs) == max_runs:
        status_message = f"Fetched runs were capped at {max_runs} due to the set limit."
    else:
        status_message = f"Fetched {len(runs)} runs successfully..."

    sample_size = config["configurable"].get("sample_size", 50)
    print(f"Sample size set to: {sample_size}")

    return {
        "all_documents": process_runs(left=[], right=runs),
        "documents": process_runs(left=[], right=runs, sample=sample_size),
        "status": [status_message],
    }
