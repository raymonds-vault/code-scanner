#!/usr/bin/env python3
"""
Start uvicorn and wait for a debugger to attach on port 5678.

Usage (from repo root):
  python scripts/run_with_debugpy.py

Then in Cursor: Run and Debug -> "code-scanner: Attach debugpy (port 5678)".

Requires: pip install -r requirements-dev.txt
"""
from __future__ import annotations

import os
import sys


def main() -> None:
    try:
        import debugpy
    except ImportError as e:
        print("Install debugpy: pip install -r requirements-dev.txt", file=sys.stderr)
        raise SystemExit(1) from e

    host = os.environ.get("DEBUGPY_HOST", "127.0.0.1")
    port = int(os.environ.get("DEBUGPY_PORT", "5678"))
    debugpy.listen((host, port))
    print(f"debugpy listening on {host}:{port} — attach from IDE, then continue…", flush=True)
    debugpy.wait_for_client()

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.environ.get("UVICORN_HOST", "127.0.0.1"),
        port=int(os.environ.get("UVICORN_PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()
