"""Embedding-based classifier for document labeling at scale."""

from typing import TYPE_CHECKING, List, Dict, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.utils import class_weight
from sklearn.metrics import accuracy_score, f1_score

from delve.state import Doc

if TYPE_CHECKING:
    from delve.console import Console


def train_classifier(
    labeled_docs: List[Doc],
    embeddings: List[List[float]],
    taxonomy: List[Dict[str, str]],
    console: Optional["Console"] = None,
) -> Tuple[RandomForestClassifier, Dict[int, str], Dict[str, float]]:
    """Train a RandomForest classifier on labeled documents.

    Args:
        labeled_docs: Documents with LLM-assigned categories
        embeddings: Embeddings for the labeled documents
        taxonomy: List of category dicts with 'id', 'name', 'description'
        console: Optional Console instance for output

    Returns:
        Tuple of (trained model, index_to_category mapping, metrics dict)
    """
    # Create mappings
    category_to_index = {cat["name"]: i for i, cat in enumerate(taxonomy)}
    index_to_category = {i: cat["name"] for i, cat in enumerate(taxonomy)}

    # Prepare training data
    X = np.array(embeddings)
    y = []
    for doc in labeled_docs:
        if doc.category not in category_to_index:
            # Skip documents with invalid categories (e.g., "Other")
            available = list(category_to_index.keys())
            if console:
                console.warning(
                    f"Skipping document with category '{doc.category}' "
                    f"not in taxonomy: {available}"
                )
            continue
        y.append(category_to_index[doc.category])

    if len(y) == 0:
        raise ValueError("No valid labeled documents to train classifier")

    y = np.array(y)

    # Filter X to match y (remove skipped documents)
    if len(y) < len(embeddings):
        valid_indices = [i for i, doc in enumerate(labeled_docs) if doc.category in category_to_index]
        X = np.array([embeddings[i] for i in valid_indices])

    # Check if we can do stratified splitting
    # We need at least 2 samples per class for stratification
    unique, counts = np.unique(y, return_counts=True)
    min_samples_per_class = counts.min()
    can_stratify = min_samples_per_class >= 2 and len(np.unique(y)) > 1

    # Split for validation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if can_stratify else None
    )

    # Calculate class weights to handle imbalanced data
    class_weights = class_weight.compute_class_weight(
        class_weight="balanced",
        classes=np.unique(y_train),
        y=y_train
    )
    class_weight_dict = dict(enumerate(class_weights))

    # Train RandomForest
    model = RandomForestClassifier(
        class_weight=class_weight_dict,
        n_estimators=100,
        random_state=42,
        n_jobs=-1  # Use all CPU cores
    )
    model.fit(X_train, y_train)

    # Evaluate
    train_preds = model.predict(X_train)
    test_preds = model.predict(X_test)

    metrics = {
        "train_accuracy": accuracy_score(y_train, train_preds),
        "test_accuracy": accuracy_score(y_test, test_preds),
        "train_f1": f1_score(y_train, train_preds, average="weighted"),
        "test_f1": f1_score(y_test, test_preds, average="weighted"),
    }

    return model, index_to_category, metrics


def predict_with_classifier(
    model: RandomForestClassifier,
    embeddings: List[List[float]],
    index_to_category: Dict[int, str],
) -> List[str]:
    """Predict categories using the trained classifier.

    Args:
        model: Trained RandomForest classifier
        embeddings: Document embeddings
        index_to_category: Mapping from class index to category name

    Returns:
        List of predicted category names
    """
    X = np.array(embeddings)
    predictions = model.predict(X)
    return [index_to_category[pred] for pred in predictions]


def get_prediction_confidence(
    model: RandomForestClassifier,
    embeddings: List[List[float]],
) -> List[float]:
    """Get confidence scores for predictions.

    Args:
        model: Trained RandomForest classifier
        embeddings: Document embeddings

    Returns:
        List of confidence scores (max probability for each prediction)
    """
    X = np.array(embeddings)
    probabilities = model.predict_proba(X)
    return [float(np.max(probs)) for probs in probabilities]
