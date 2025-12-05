"""Node for loading data using adapters."""

import random
from typing import List
from langchain_core.runnables import RunnableConfig

from delve.state import State, Doc
from delve.configuration import Configuration


async def load_data(state: State, config: RunnableConfig) -> dict:
    """Load documents using the configured adapter.

    This node expects that documents have already been loaded by the adapter
    and passed into the state. It performs sampling if configured.

    Args:
        state: Current application state with documents
        config: Configuration for the run

    Returns:
        dict: Updated state fields with sampled documents
    """
    configuration = Configuration.from_runnable_config(config)

    # Documents should already be in state.all_documents
    # (loaded by SDK/CLI before invoking the graph)
    all_docs = state.all_documents

    if not all_docs:
        raise ValueError("No documents found in state. Documents should be loaded before invoking the graph.")

    # Sample documents if sample_size is configured
    sample_size = configuration.sample_size

    if sample_size and sample_size < len(all_docs):
        # Random sample
        sampled_docs = random.sample(all_docs, sample_size)
        status_message = f"Sampled {sample_size} documents from {len(all_docs)} total documents"
    else:
        # Use all documents
        sampled_docs = all_docs
        status_message = f"Processing all {len(all_docs)} documents"

    return {
        "documents": sampled_docs,
        "status": [status_message],
    }
