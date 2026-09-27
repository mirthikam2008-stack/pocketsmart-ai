"""
PocketSmart AI - Application Entry Point (Forwarder to Backend)
"""

import uvicorn
from backend.main import app

if __name__ == "__main__":
    print("[PocketSmart AI] Starting Server from backend.main on http://127.0.0.1:8000")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
