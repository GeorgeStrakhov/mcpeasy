"""
Multi-MCP Server - Main FastAPI application with token-based routing
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
import time
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastmcp import FastMCP
from dotenv import load_dotenv

from .database import DatabaseService
from .server.factory import MCPServerFactory
from .admin import admin_router
from .tools.registry import tool_registry

load_dotenv()

# Configure logging
def setup_logging():
    """Configure application logging"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Reduce noise from external libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    # Set our app loggers
    logging.getLogger("mcpeasy").setLevel(getattr(logging, log_level))

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Initialize database
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    app.state.db = DatabaseService(database_url)
    await app.state.db.initialize()
    
    # Initialize MCP server factory
    app.state.mcp_factory = MCPServerFactory(app.state.db)
    
    # Start the tool execution queue
    await tool_registry.ensure_queue_started()
    
    yield
    
    # Cleanup
    await app.state.db.close()


app = FastAPI(
    title="Multi-MCP Server",
    description="Production-grade multi-MCP server with token-based routing",
    version="0.1.0",
    lifespan=lifespan
)

# Add session middleware
session_secret = os.getenv("SESSION_SECRET", "your-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=session_secret)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount admin interface
app.include_router(admin_router, prefix="/admin", tags=["admin"])

# Mount static files in production
if os.getenv("PRODUCTION") == "true":
    static_path = "/app/static"
    if os.path.exists(static_path):
        # Mount assets directory for JS/CSS files
        app.mount("/assets", StaticFiles(directory=f"{static_path}/assets"), name="assets")
        
        # Mount static files for other static assets (images, etc.)
        app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def root(request: Request):
    """Root endpoint - serves React app in production, API info in development"""
    # In production, this will be handled by the catch-all route above
    # This endpoint only runs in development
    if os.getenv("PRODUCTION") == "true":
        # This shouldn't be reached in production due to catch-all route
        from fastapi.responses import FileResponse
        return FileResponse("/app/static/index.html")
    else:
        return {"message": "MCPeasy Server is running"}


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint with database connectivity"""
    db: DatabaseService = request.app.state.db
    db_healthy = await db.health_check()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/metrics/queue")
async def queue_metrics():
    """Get current queue statistics"""
    return tool_registry.get_queue_stats()


# Catch-all route for React Router (must be last)
if os.getenv("PRODUCTION") == "true":
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React app for any non-API routes (React Router)"""
        # Don't serve React app for API routes, static assets, or specific endpoints
        if full_path.startswith(("admin/api", "mcp", "health", "assets", "static")):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Serve index.html for all other routes (React Router)
        from fastapi.responses import FileResponse
        return FileResponse("/app/static/index.html")


@app.api_route("/mcp/{token}", methods=["GET", "POST", "OPTIONS"])
async def mcp_handler(token: str, request: Request, background_tasks: BackgroundTasks):
    """
    Handle MCP requests with hybrid token/API key routing for backward compatibility
    Supports both legacy tokens and new API keys
    """
    try:
        # Handle CORS preflight
        if request.method == "OPTIONS":
            return Response(
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                }
            )
        
        # Try new API key system first
        mcp_server = await app.state.mcp_factory.get_server(token)
        if mcp_server:
            # New API key system
            return await mcp_server.handle_request(request, background_tasks)
        
        # Fallback to legacy token system
        db: DatabaseService = request.app.state.db
        server_config = await db.get_server_config(token)
        if server_config:
            # Legacy token system
            mcp_server = await app.state.mcp_factory.get_server_legacy(server_config)
            return await mcp_server.handle_request(request, background_tasks)
        
        # Neither system recognizes this token/key
        raise HTTPException(status_code=401, detail="Invalid token or API key")
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error and return a proper error response
        logger.error(f"Error in MCP handler: {e}", exc_info=True)
        
        # Return a JSON error response instead of letting it bubble up
        return Response(
            content='{"error": "Internal server error"}',
            status_code=500,
            media_type="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )