"""Node for labeling documents using the generated taxonomy.

Uses a hybrid approach:
1. LLM labels sampled documents (training set)
2. If there are more documents, trains a classifier and uses it for the rest
3. Returns all labeled documents
"""

import re
from typing import Dict, Any, List
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_openai import OpenAIEmbeddings

from delve.state import State, Doc
from delve.utils import load_chat_model
from delve.configuration import Configuration
from delve.prompts import LABELER_PROMPT
from delve.core.classifier import train_classifier, predict_with_classifier


def _get_category_name_by_id(category_id: str, taxonomy: List[Dict[str, str]]) -> str:
    """Map category ID to category name.

    Args:
        category_id: The category ID as string
        taxonomy: List of category dicts with 'id', 'name', 'description'

    Returns:
        Category name

    Raises:
        ValueError: If ID not found in taxonomy
    """
    for cat in taxonomy:
        if str(cat["id"]) == str(category_id):
            return cat["name"]

    # ID not found
    available_ids = [cat["id"] for cat in taxonomy]
    raise ValueError(
        f"Category ID '{category_id}' not found in taxonomy. "
        f"Available IDs: {available_ids}"
    )


def _parse_labels(output_text: str, console=None) -> Dict[str, str]:
    """Parse the generated category ID from LLM output."""
    # Extract category ID from <category_id>N</category_id> tags
    id_matches = re.findall(
        r"<category_id>\s*(\d+)\s*</category_id>",
        output_text,
        re.DOTALL,
    )

    if not id_matches:
        # Fallback: try to find any number in the output
        if console:
            console.warning(f"No <category_id> tag found in output: {output_text[:200]}")
        return {"category_id": None}

    if len(id_matches) > 1:
        if console:
            console.warning(f"Multiple category IDs found: {id_matches}, using first one")

    return {"category_id": id_matches[0]}


def _format_taxonomy(clusters: List[Dict[str, str]]) -> str:
    """Format taxonomy clusters as XML."""

    xml = "<cluster_table>\n"

    if clusters and isinstance(clusters[0], list):
        clusters = clusters[0]

    if isinstance(clusters, dict):
        clusters = [clusters]

    for cluster in clusters:
        xml += "  <cluster>\n"
        if isinstance(cluster, dict):
            xml += f'    <id>{cluster["id"]}</id>\n'
            xml += f'    <name>{cluster["name"]}</name>\n'
            xml += f'    <description>{cluster["description"]}</description>\n'
        else:
            xml += f'    <id>{getattr(cluster, "id", "")}</id>\n'
            xml += f'    <name>{getattr(cluster, "name", "")}</name>\n'
            xml += f'    <description>{getattr(cluster, "description", "")}</description>\n'
        xml += "  </cluster>\n"
    xml += "</cluster_table>"
    return xml


def _setup_classification_chain(configuration: Configuration):
    """Set up the chain for document labeling."""
    model = load_chat_model(configuration.fast_llm)

    return (
        LABELER_PROMPT
        | model
        | StrOutputParser()
        | _parse_labels
    ).with_config(run_name="LabelDocs")


async def label_documents(
    state: State,
    config: RunnableConfig,
) -> dict:
    """Label documents using LLM + classifier approach.

    Strategy:
    1. LLM labels sampled documents (state.documents)
    2. If more documents exist in state.all_documents:
       - Train RandomForest classifier on embeddings
       - Use classifier to label remaining documents
    3. Return all labeled documents
    """
    configuration = Configuration.from_runnable_config(config)
    console = configuration.get_console()

    # Debug: Show configuration
    console.debug(f"Configuration: model={configuration.model}, fast_llm={configuration.fast_llm}")
    console.debug(f"Sample size: {configuration.sample_size}, Batch size: {configuration.batch_size}")
    console.debug(f"Documents to label: {len(state.documents)}, Total documents: {len(state.all_documents)}")

    # Get latest taxonomy
    latest_clusters = None
    for clusters in reversed(state.clusters):
        if isinstance(clusters, list) and clusters:
            latest_clusters = clusters
            break

    if not latest_clusters and state.clusters:
        latest_clusters = [state.clusters[-1]] if isinstance(state.clusters[-1], dict) else state.clusters[-1]

    if not latest_clusters:
        raise ValueError("No valid clusters found in state")

    # Debug: Show taxonomy categories
    console.debug(f"Taxonomy has {len(latest_clusters)} categories:")
    for cat in latest_clusters:
        console.debug(f"  [{cat['id']}] {cat['name']}")

    # Step 1: Label sampled documents with LLM
    labeling_chain = _setup_classification_chain(configuration)

    # Process documents with progress tracking
    labeled_results = []
    with console.progress(len(state.documents), "Labeling documents with LLM") as advance:
        for doc in state.documents:
            result = await labeling_chain.ainvoke(
                {
                    "content": doc["content"] if isinstance(doc, dict) else doc.content,
                    "taxonomy": _format_taxonomy(latest_clusters),
                }
            )
            labeled_results.append(result)
            advance()

    # Create labeled Doc objects for sampled documents
    # Map category IDs to category names
    llm_labeled_docs = []
    warnings_list = []
    other_count = 0

    for doc, category_result in zip(state.documents, labeled_results):
        category_id = category_result.get("category_id")

        if category_id is None:
            warning_msg = f"No category ID returned for doc {doc['id'] if isinstance(doc, dict) else doc.id}, using 'Other'"
            console.warning(warning_msg)
            warnings_list.append(warning_msg)
            category_name = "Other"
            other_count += 1
        else:
            try:
                category_name = _get_category_name_by_id(category_id, latest_clusters)
            except ValueError as e:
                warning_msg = f"{e}, using 'Other'"
                console.warning(warning_msg)
                warnings_list.append(warning_msg)
                category_name = "Other"
                other_count += 1

        llm_labeled_docs.append(Doc(
            id=doc["id"] if isinstance(doc, dict) else doc.id,
            content=doc["content"] if isinstance(doc, dict) else doc.content,
            summary=doc.get("summary", "") if isinstance(doc, dict) else (doc.summary or ""),
            explanation=None,
            category=category_name
        ))

    # Step 2: Check if we need to label more documents
    total_docs = len(state.all_documents)
    sampled_docs = len(state.documents)

    if sampled_docs >= total_docs:
        # All documents were sampled and labeled by LLM
        console.success(f"All {total_docs} documents labeled by LLM")

        return {
            "documents": llm_labeled_docs,
            "status": [f"All {total_docs} documents labeled by LLM"],
            "llm_labeled_count": len(llm_labeled_docs),
            "classifier_labeled_count": 0,
            "skipped_document_count": other_count,
            "warnings": warnings_list,
        }

    # Step 3: Train classifier and label remaining documents
    remaining_count = total_docs - sampled_docs
    console.info(f"Training classifier on {sampled_docs} LLM-labeled documents...")
    console.info(f"  Will classify {remaining_count} remaining documents")

    # Initialize embeddings encoder
    encoder = OpenAIEmbeddings(model=configuration.embedding_model)

    # Generate embeddings for LLM-labeled documents (training set)
    with console.status("Generating embeddings for training set..."):
        training_contents = [doc.content for doc in llm_labeled_docs]
        training_embeddings = await encoder.aembed_documents(training_contents)

    # Train classifier
    with console.status("Training RandomForest classifier..."):
        model, index_to_category, metrics = train_classifier(
            llm_labeled_docs,
            training_embeddings,
            latest_clusters,
            console=console,
        )

    console.success(
        f"Classifier trained - Test F1: {metrics['test_f1']:.3f}, "
        f"Test Accuracy: {metrics['test_accuracy']:.3f}"
    )
    console.debug(f"Classifier metrics detail:")
    console.debug(f"  Train Accuracy: {metrics['train_accuracy']:.3f}, Train F1: {metrics['train_f1']:.3f}")
    console.debug(f"  Test Accuracy: {metrics['test_accuracy']:.3f}, Test F1: {metrics['test_f1']:.3f}")

    # Get unlabeled documents (those not in the sample)
    sampled_ids = {doc.id for doc in llm_labeled_docs}
    unlabeled_docs = [
        doc for doc in state.all_documents
        if (doc["id"] if isinstance(doc, dict) else doc.id) not in sampled_ids
    ]

    # Generate embeddings for unlabeled documents
    with console.status(f"Generating embeddings for {len(unlabeled_docs)} documents..."):
        unlabeled_contents = [
            doc["content"] if isinstance(doc, dict) else doc.content
            for doc in unlabeled_docs
        ]
        unlabeled_embeddings = await encoder.aembed_documents(unlabeled_contents)

    # Predict categories
    with console.status("Classifying with trained model..."):
        predicted_categories = predict_with_classifier(
            model,
            unlabeled_embeddings,
            index_to_category
        )

    # Create Doc objects for classifier-labeled documents
    classifier_labeled_docs = [
        Doc(
            id=doc["id"] if isinstance(doc, dict) else doc.id,
            content=doc["content"] if isinstance(doc, dict) else doc.content,
            summary=doc.get("summary", "") if isinstance(doc, dict) else (doc.summary or ""),
            explanation=None,
            category=category
        )
        for doc, category in zip(unlabeled_docs, predicted_categories)
    ]

    # Combine all labeled documents
    all_labeled_docs = llm_labeled_docs + classifier_labeled_docs

    console.success(f"Total labeled: {len(all_labeled_docs)} documents")
    console.info(f"  - {len(llm_labeled_docs)} by LLM")
    console.info(f"  - {len(classifier_labeled_docs)} by classifier")

    return {
        "documents": all_labeled_docs,
        "status": [
            f"Labeled {len(llm_labeled_docs)} documents with LLM",
            f"Trained classifier (F1: {metrics['test_f1']:.3f})",
            f"Classified {len(classifier_labeled_docs)} documents with model",
            f"Total: {len(all_labeled_docs)} documents labeled"
        ],
        "classifier_metrics": metrics,
        "llm_labeled_count": len(llm_labeled_docs),
        "classifier_labeled_count": len(classifier_labeled_docs),
        "skipped_document_count": other_count,
        "warnings": warnings_list,
    }
