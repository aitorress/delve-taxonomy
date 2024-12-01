"""Node for updating taxonomies based on new document batches."""

from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig

from react_agent.state import State
from react_agent.utils import load_chat_model, parse_taxa, invoke_taxonomy_chain
from react_agent.configuration import Configuration


def _setup_update_chain(model_name: str, max_tokens: int):
    """Set up the chain for taxonomy updates.
    
    Args:
        model_name: Name of the model to use
        max_tokens: Maximum tokens for model response
        
    Returns:
        Chain for updating and parsing taxonomies
    """
    # Initialize the prompt
    update_prompt = hub.pull("wfh/tnt-llm-taxonomy-update")

    # Create the chain
    model = load_chat_model(
        f"anthropic/{model_name}",
    )

    return (
        update_prompt
        | model
        | StrOutputParser()
        | parse_taxa
    ).with_config(run_name="UpdateTaxonomy")


async def update_taxonomy(
    state: State,
    config: RunnableConfig,
    model_name: str = "claude-3-haiku-20240307",
    max_tokens: int = 2000,
) -> dict:
    """Update taxonomy using the next batch of documents.
    
    Args:
        state: Current application state
        config: Configuration for the run
        model_name: Name of the model to use
        max_tokens: Maximum tokens for model response
        
    Returns:
        dict: Updated state fields with revised taxonomy
    """
    configuration = Configuration.from_runnable_config(config)
    
    # Set up the chain
    update_chain = _setup_update_chain(model_name, max_tokens)

    # Determine which minibatch to use
    which_mb = len(state.clusters) % len(state.minibatches)

    # Update taxonomy using the next batch
    return await invoke_taxonomy_chain(
        update_chain,
        state,
        config,
        state.minibatches[which_mb]
    )
