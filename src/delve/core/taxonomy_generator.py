"""Node for generating taxonomies from document batches."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig

from delve.state import State
from delve.utils import load_chat_model, parse_taxa, invoke_taxonomy_chain
from delve.configuration import Configuration
from delve.prompts import TAXONOMY_GENERATION_PROMPT

def _setup_taxonomy_chain(configuration: Configuration, feedback: str):
    """Set up the chain for taxonomy generation."""
    # Initialize the prompt with default use case
    taxonomy_prompt = TAXONOMY_GENERATION_PROMPT.partial(
        use_case="Generate the taxonomy that can be used to label the user intent in the conversation.",
        feedback=feedback,
    )
    # Create the chain
    model = load_chat_model(
        configuration.fast_llm,
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
    
    # Set up the chain
    taxonomy_chain = _setup_taxonomy_chain(configuration, feedback)

    # Generate taxonomy using the first batch
    return await invoke_taxonomy_chain(
        taxonomy_chain,
        state,
        config,
        state.minibatches[0],
    )
