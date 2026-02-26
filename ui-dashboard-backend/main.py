from __future__ import annotations

import os

import uvicorn

from app import app


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("DASHBOARD_BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("DASHBOARD_BACKEND_PORT", "3001")),
        reload=False,
    )
