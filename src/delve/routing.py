"""Routing logic for the taxonomy generation graph."""

from typing import Literal

from delve.state import State


def should_review(state: State) -> Literal["update_taxonomy", "review_taxonomy"]:
    """Determine whether to continue updating or move to review.

    Checks if all minibatches have been processed.

    Args:
        state: Current state

    Returns:
        "update_taxonomy" if more batches to process, "review_taxonomy" if done
    """
    num_minibatches = len(state.minibatches)
    num_revisions = len(state.clusters)
    if num_revisions < num_minibatches:
        return "update_taxonomy"
    return "review_taxonomy"
