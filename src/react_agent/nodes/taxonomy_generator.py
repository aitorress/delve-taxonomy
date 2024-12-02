"""Node for generating taxonomies from document batches."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig

from react_agent.state import State
from react_agent.utils import load_chat_model, parse_taxa, invoke_taxonomy_chain
from react_agent.configuration import Configuration
from react_agent.prompts import TAXONOMY_GENERATION_PROMPT

def _setup_taxonomy_chain(model_name: str, max_tokens: int, anthropic_api_key: str):
    """Set up the chain for taxonomy generation."""
    # Initialize the prompt with default use case
    taxonomy_prompt = TAXONOMY_GENERATION_PROMPT.partial(
        use_case="Generate the taxonomy that can be used to label the user intent in the conversation.",
    )

    # Create the chain
    model = load_chat_model(
        f"anthropic/{model_name}",
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
    model_name: str = "claude-3-haiku-20240307",
    max_tokens: int = 2000,
) -> dict:
    """Generate taxonomy from the first batch of documents."""
    configuration = Configuration.from_runnable_config(config)
    
    # Set up the chain
    taxonomy_chain = _setup_taxonomy_chain(
        model_name, 
        max_tokens,
        configuration.anthropic_api_key
    )

    # Format the feedback if it exists
    feedback = "No previous feedback provided."
    if state.user_feedback:
        feedback = f"Previous user feedback: {state.user_feedback.get('feedback', '')}"
        if state.user_feedback.get('explanation'):
            feedback += f"\nReason for modification: {state.user_feedback['explanation']}"

    print(f"Generator Feedback: {feedback}")

    # Generate taxonomy using the first batch
    return await invoke_taxonomy_chain(
        taxonomy_chain,
        state,
        config,
        state.minibatches[0],
    )
