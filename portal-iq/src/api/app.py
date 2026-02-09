"""
FastAPI Application

Main application factory and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from ..utils.config import Config


def create_app(config: Config = None) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        config: Optional configuration object

    Returns:
        Configured FastAPI application
    """
    if config is None:
        config = Config()

    app = FastAPI(
        title="Portal IQ API",
        description=(
            "AI-powered transfer portal and NIL intelligence platform "
            "for college football. Built by Elite Sports Solutions."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware - restricted origins in production
    import os
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        allowed_origins = [
            "https://playmakervc.com",
            "https://www.playmakervc.com",
            "https://portal-iq.streamlit.app",
            "https://portaliq.app",
        ]
        # Add any additional origins from environment
        extra_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
        if extra_origins:
            allowed_origins.extend([o.strip() for o in extra_origins.split(",") if o.strip()])
    else:
        allowed_origins = ["*"]  # Allow all in development only

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Store config in app state
    app.state.config = config

    # Include routers
    app.include_router(router, prefix="/api/v1")

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Portal IQ API",
            "version": "1.0.0",
            "description": "AI-powered transfer portal and NIL intelligence",
            "docs": "/docs",
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


# Create default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
