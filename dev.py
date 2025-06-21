#!/usr/bin/env python3
"""
Development server runner with enhanced live reload
"""
import os
import sys
import argparse
import uvicorn
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Run development server")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)), help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    # Enhanced reload configuration for Docker
    reload_config = None
    if args.reload:
        reload_config = {
            "reload": True,
            "reload_dirs": ["src"],
            "reload_includes": ["*.py"],
            "reload_excludes": ["*.pyc", "__pycache__"],
        }
        # If in Docker, use polling for cross-platform compatibility
        if os.getenv("DEVELOPMENT") == "true":
            reload_config["reload_delay"] = 0.25
    
    uvicorn.run(
        "src.main:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        **(reload_config if reload_config else {"reload": False})
    )

if __name__ == "__main__":
    main()