"""FastAPI server for Delve taxonomy generation.

This module provides a REST API for exposing Delve functionality
to JavaScript/TypeScript frontends and other HTTP clients.
"""

from delve.api.server import app, create_app

__all__ = ["app", "create_app"]
