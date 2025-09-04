#!/usr/bin/env python3
"""
Optimized startup script for AI Ultimate Assistant
Disables file watching and improves performance
"""
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Set environment variables for better performance
    os.environ["WATCHFILES_FORCE_POLLING"] = "false"
    os.environ["WATCHFILES_IGNORE_PATTERNS"] = "*.pyc,*.pyo,__pycache__,*.log"
    
    # Disable file watching for better performance
    os.environ["WATCHFILES_DISABLE"] = "true"
    
    # Configure uvicorn for better performance
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disable auto-reload for better performance
        workers=1,     # Single worker for development
        log_level="info",
        access_log=True,
        loop="asyncio",
        http="httptools",  # Faster HTTP parser
        ws="websockets",   # WebSocket support
        lifespan="on",
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30,
    ) 