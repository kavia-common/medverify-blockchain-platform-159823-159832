#!/usr/bin/env python3
"""
Container startup script for medical_prescription_database.

Behavior:
- Resolve SQLITE_DB path
- Run database migrations (idempotent)
- Persist connection info and db_visualizer env
- Start an HTTP health server on the configured port (default 5001)

Environment:
- SQLITE_DB: path to SQLite file (default: ./myapp.db)
- PORT or HEALTH_PORT: port for health server (default: 5001)
"""

import os
import sys
import traceback

from init_db import (
    get_db_path as resolve_db_path,
    run_migrations,
    write_connection_info,
    write_visualizer_env,
)
from health_server import run_health_server


# PUBLIC_INTERFACE
def main() -> None:
    """Entrypoint: initialize DB and start a health server."""
    db_path = resolve_db_path()
    print(f"[startup] Using database path: {db_path}")

    # Ensure parent dir exists if a nested path is provided
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    try:
        print("[startup] Running migrations...")
        run_migrations()
        print("[startup] Migrations completed.")
    except Exception as e:
        print(f"[startup] Migration failed: {e}")
        traceback.print_exc()
        # Exit with non-zero to signal container failure
        sys.exit(1)

    # Write helper files (best-effort)
    try:
        write_connection_info(db_path)
        write_visualizer_env(db_path)
    except Exception as e:
        print(f"[startup] Warning: failed writing helper files: {e}")

    # Determine health server port
    port = int(os.getenv("PORT", os.getenv("HEALTH_PORT", "5001")))
    print(f"[startup] Starting health server on port {port}...")
    run_health_server(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
