#!/usr/bin/env python3
"""
Lightweight HTTP health server for the SQLite database container.

- Binds to 0.0.0.0 on configurable port (default 5001)
- Provides /health endpoint returning JSON with DB readiness details
- Uses SQLITE_DB env var (or ./myapp.db) to locate the database file
"""

import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Tuple

REQUIRED_TABLES = {
    "roles",
    "users",
    "user_roles",
    "prescriptions",
    "prescription_blockchain_refs",
    "prescription_audit_logs",
    "prescription_metadata",
    "schema_migrations",
}


# PUBLIC_INTERFACE
def get_db_path() -> str:
    """Return the path to the SQLite database file using the SQLITE_DB env var or default to 'myapp.db'."""
    return os.getenv("SQLITE_DB", "myapp.db")


def _table_exists(cur: sqlite3.Cursor, name: str) -> bool:
    """Check if a table exists in the SQLite database."""
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


# PUBLIC_INTERFACE
def check_db_health() -> Tuple[bool, Dict]:
    """Check database health: file presence, connection, required tables."""
    db_path = get_db_path()
    info: Dict = {"db_path": db_path, "exists": False, "sqlite_version": None, "missing_tables": []}

    if not os.path.exists(db_path):
        return False, {**info, "exists": False, "error": "Database file not found"}

    info["exists"] = True

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("SELECT sqlite_version()")
        info["sqlite_version"] = cur.fetchone()[0]

        missing = [t for t in REQUIRED_TABLES if not _table_exists(cur, t)]
        info["missing_tables"] = sorted(missing)
        ok = len(missing) == 0
        return ok, info
    except sqlite3.Error as e:
        return False, {**info, "error": f"Connection failed: {e}"}
    finally:
        try:
            conn.close()  # type: ignore[name-defined]
        except Exception:
            pass


class _HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler serving health endpoints."""

    def _send_json(self, code: int, payload: Dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        """Serve GET requests: /health or /"""
        if self.path.startswith("/health") or self.path == "/":
            ok, info = check_db_health()
            payload = {"status": "ok" if ok else "error", **info}
            self._send_json(200 if ok else 503, payload)
        else:
            self._send_json(404, {"error": "Not found"})

    def log_message(self, format, *args):  # noqa: A003
        # Reduce noisy default logging; print concise messages instead
        msg = "%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args)
        try:
            print(msg, flush=True)
        except Exception:
            pass


# PUBLIC_INTERFACE
def run_health_server(host: str = "0.0.0.0", port: int = 5001) -> None:
    """Run the health server at the specified host and port until interrupted."""
    server = HTTPServer((host, port), _HealthHandler)
    print(f"Health server listening on http://{host}:{port} (CTRL+C to stop)")
    server.serve_forever()


if __name__ == "__main__":
    # Allow running directly for local testing
    p = int(os.getenv("PORT", os.getenv("HEALTH_PORT", "5001")))
    run_health_server(port=p)
