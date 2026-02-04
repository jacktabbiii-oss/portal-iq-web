"""Portal IQ API for external integrations.

This module provides a FastAPI-based API layer for integrating
Portal IQ data with external applications like playmakervc.com.

Usage:
    # Run standalone API server
    uvicorn dashboard.api:app --host 0.0.0.0 --port 8000

    # Or import and mount in existing FastAPI app
    from dashboard.api import app as portal_iq_api
"""

from dashboard.api.main import app, create_app

__all__ = ["app", "create_app"]
