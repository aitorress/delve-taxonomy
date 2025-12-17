"""Node for generating summaries of documents."""

import re
from typing import Dict, List, Any
from uuid import uuid4

from langsmith import Client
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableConfig

from delve.state import State
from delve.utils import load_chat_model, parse_taxa, invoke_taxonomy_chain
from delve.configuration import Configuration


def _get_content(state: Dict[str, List]) -> List[Dict[str, str]]:
    """Extract content from documents for summarization.
    
    Args:
        state: State dictionary containing documents
        
    Returns:
        List of document contents formatted for summarization
    """
    docs = state["documents"]
    return [
        {
            "content": (
                doc["content"] if isinstance(doc, dict) 
                else doc.content
            )
        }
        for doc in docs
    ]


def _parse_summary(xml_string: str) -> dict:
    """Parse summary and explanation from XML string.
    
    Args:
        xml_string: XML formatted string containing summary and explanation
        
    Returns:
        dict: Parsed summary and explanation
    """
    summary_pattern = r"<summary>(.*?)</summary>"
    explanation_pattern = r"<explanation>(.*?)</explanation>"

    summary_match = re.search(summary_pattern, xml_string, re.DOTALL)
    explanation_match = re.search(explanation_pattern, xml_string, re.DOTALL)

    summary = summary_match.group(1).strip() if summary_match else ""
    explanation = explanation_match.group(1).strip() if explanation_match else ""

    return {"summary": summary, "explanation": explanation}


def _reduce_summaries(combined: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Combine documents with their summaries.
    
    Args:
        combined: Dictionary containing documents and their summaries
        
    Returns:
        dict: Documents enriched with summaries and explanations
    """
    summaries = combined["summaries"]
    documents = combined["documents"]
    return {
        "documents": [
            {
                "id": doc.get("id", str(uuid4())),
                "content": doc.get("content", ""),
                "summary": summ_info.get("summary", ""),
                "explanation": summ_info.get("explanation", ""),
            }
            for doc, summ_info in zip(documents, summaries)
        ],
        "status": ["Summarized successfully."],
    }


async def generate_summaries(
    state: State,
    config: RunnableConfig,
    model_name: str = "claude-haiku-4-5-20251001",
) -> dict:
    """Generate summaries for a collection of documents."""

    client = Client()

    configuration = Configuration.from_runnable_config(config)

    # Initialize the model and prompt
    try:
        model = load_chat_model(configuration.fast_llm)
    except (ValueError, TypeError) as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            raise ValueError(
                f"Authentication failed when loading model '{configuration.fast_llm}'.\n\n"
                f"{error_msg}\n\n"
                f"Please verify your ANTHROPIC_API_KEY is set correctly:\n"
                f"  export ANTHROPIC_API_KEY=your-api-key-here\n\n"
                f"You can get an API key from: https://console.anthropic.com/"
            ) from e
        raise
    
    summary_prompt = client.pull_prompt("wfh/tnt-llm-summary-generation").partial(
        summary_length=20, explanation_length=30
    )

    # Create the summary chain
    summary_llm_chain = (
        summary_prompt 
        | model 
        | StrOutputParser()
    ).with_config(run_name="GenerateSummary")

    summary_chain = summary_llm_chain | _parse_summary

    # Create the full chain with map-reduce
    map_reduce_chain = (
        RunnablePassthrough.assign(
            summaries=_get_content
            | RunnableLambda(func=summary_chain.batch, afunc=summary_chain.abatch)
        )
        | _reduce_summaries
    )

    # Process documents
    processed_docs = []
    for doc in state.documents:
        if isinstance(doc, str):
            processed_docs.append({"id": str(uuid4()), "content": doc})
        elif isinstance(doc, dict):
            if "id" not in doc:
                doc["id"] = str(uuid4())
            processed_docs.append(doc)
        else:
            processed_docs.append({"id": str(uuid4()), "content": str(doc)})

    try:
        return await map_reduce_chain.ainvoke({"documents": processed_docs})
    except (TypeError, ValueError) as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "could not resolve" in error_msg.lower():
            raise ValueError(
                f"Authentication failed during document summarization.\n\n"
                f"The API key is missing or invalid. Please verify:\n"
                f"  export ANTHROPIC_API_KEY=your-api-key-here\n\n"
                f"Get your API key from: https://console.anthropic.com/\n\n"
                f"Original error: {error_msg}"
            ) from e
        raise
