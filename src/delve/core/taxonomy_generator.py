"""Node for generating taxonomies from document batches."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig

from delve.state import State
from delve.utils import load_chat_model, parse_taxa, invoke_taxonomy_chain
from delve.configuration import Configuration
from delve.prompts import TAXONOMY_GENERATION_PROMPT

def _setup_taxonomy_chain(configuration: Configuration, feedback: str, use_case: str):
    """Set up the chain for taxonomy generation."""
    # Use the configured use_case, or fallback to default if empty
    effective_use_case = use_case if use_case else "Generate the taxonomy that can be used to label the user intent in the conversation."
    taxonomy_prompt = TAXONOMY_GENERATION_PROMPT.partial(
        use_case=effective_use_case,
        feedback=feedback,
    )
    # Create the chain - use main model for taxonomy generation (core reasoning task)
    model = load_chat_model(
        configuration.model,
    )

    return (
        taxonomy_prompt
        | model
        | StrOutputParser()
        | parse_taxa
    ).with_config(run_name="GenerateTaxonomy")


async def generate_taxonomy(
    state: State,
    config: RunnableConfig,
) -> dict:
    """Generate taxonomy from the first batch of documents."""
    configuration = Configuration.from_runnable_config(config)

    # Format the feedback (non-interactive mode, no user feedback)
    feedback = "No previous feedback provided."
    
    # Use use_case from state (populated from configuration in data_loader)
    use_case = state.use_case if state.use_case else configuration.use_case
    
    # Set up the chain with the actual use_case
    taxonomy_chain = _setup_taxonomy_chain(configuration, feedback, use_case)

    # Generate taxonomy using the first batch
    return await invoke_taxonomy_chain(
        taxonomy_chain,
        state,
        config,
        state.minibatches[0],
    )
