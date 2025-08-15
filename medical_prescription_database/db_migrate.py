#!/usr/bin/env python3
"""SQLite migration runner for the medical_prescription_database.

This script applies SQL migrations in order and records their application in a schema_migrations table.
It uses the SQLITE_DB environment variable to locate the database file; if not set, defaults to myapp.db.

Usage:
  - python db_migrate.py migrate     # Apply all pending migrations
  - python db_migrate.py status      # Show applied and pending migrations
  - python db_migrate.py reset       # Danger: Delete DB file and re-run migrations (local/dev only)

Environment:
  - SQLITE_DB: Absolute or relative path to SQLite file. Example: /path/to/myapp.db

Notes:
  - Foreign keys are enabled during migration execution (PRAGMA foreign_keys = ON).
  - Migrations are plain .sql files in ./migrations, executed with executescript.
"""

import os
import sys
import glob
import hashlib
import sqlite3
from datetime import datetime
from typing import List, Tuple

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")

# PUBLIC_INTERFACE
def get_db_path() -> str:
    """Return the path to the SQLite database file using the SQLITE_DB env var or default to 'myapp.db'."""
    db_path = os.getenv("SQLITE_DB", "myapp.db")
    return db_path

def _connect(db_path: str) -> sqlite3.Connection:
    """Create a sqlite3 connection."""
    conn = sqlite3.connect(db_path)
    # Ensure foreign keys are enforced for this connection
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    """Create schema_migrations table if it doesn't exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()

def _file_checksum(path: str) -> str:
    """Return SHA256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _list_migration_files() -> List[str]:
    """List migrations in ascending order (0001_*.sql, 0002_*.sql, ...)."""
    files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    return files

def _applied_migrations(conn: sqlite3.Connection) -> List[Tuple[str, str]]:
    """Return list of (filename, checksum) of already applied migrations."""
    cur = conn.execute("SELECT filename, checksum FROM schema_migrations ORDER BY filename")
    return list(cur.fetchall())

def _validate_applied_checksums(conn: sqlite3.Connection) -> None:
    """Check if already-applied migration checksums still match their files; warn if drift is detected."""
    applied = _applied_migrations(conn)
    for filename, prior_checksum in applied:
        file_path = os.path.join(MIGRATIONS_DIR, filename)
        if os.path.exists(file_path):
            current_checksum = _file_checksum(file_path)
            if current_checksum != prior_checksum:
                print(f"WARNING: Checksum mismatch for applied migration {filename}. File may have changed.")
        else:
            print(f"WARNING: Migration file {filename} no longer exists on disk.")

def _ensure_users_public_id_column(conn: sqlite3.Connection) -> None:
    """Preflight: ensure users.public_id exists for backward-compat and create index if missing.

    This avoids relying on 'ALTER TABLE ... ADD COLUMN IF NOT EXISTS', which some SQLite versions don't support,
    and prevents later index migrations from failing if the column is missing. Idempotent and safe.
    """
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cur.fetchall()}
        if "public_id" not in cols:
            # Temporarily disable FK enforcement for schema change safety
            conn.execute("PRAGMA foreign_keys = OFF")
            try:
                conn.execute("ALTER TABLE users ADD COLUMN public_id TEXT")
                print("✓ Preflight: added users.public_id column")
            finally:
                conn.execute("PRAGMA foreign_keys = ON")
            conn.commit()

        # Try to create index (no-op if exists)
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_public_id ON users(public_id)")
            conn.commit()
        except sqlite3.Error:
            # If index creation fails due to very old SQLite, subsequent migrations may handle it.
            pass
    except sqlite3.Error as e:
        print(f"WARNING: Preflight ensure public_id column failed (continuing): {e}")

# PUBLIC_INTERFACE
def migrate() -> None:
    """Apply all pending migrations."""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    conn = _connect(db_path)
    try:
        _ensure_migrations_table(conn)

        # Preflight compatibility fix: make sure users.public_id exists before running .sql files.
        _ensure_users_public_id_column(conn)

        _validate_applied_checksums(conn)

        applied_map = {fn: ch for fn, ch in _applied_migrations(conn)}
        pending = []
        for path in _list_migration_files():
            filename = os.path.basename(path)
            checksum = _file_checksum(path)
            if filename not in applied_map:
                pending.append((filename, checksum, path))

        if not pending:
            print("No pending migrations. Database is up to date.")
            return

        print(f"Applying {len(pending)} migration(s)...")
        for filename, checksum, path in pending:
            print(f"  -> {filename}")
            with open(path, "r", encoding="utf-8") as f:
                sql = f.read()
            try:
                with conn:
                    conn.executescript("PRAGMA foreign_keys = ON;")
                    if sql.strip():
                        conn.executescript(sql)
                    conn.execute(
                        "INSERT INTO schema_migrations (filename, checksum, applied_at) VALUES (?, ?, ?)",
                        (filename, checksum, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
                    )
            except sqlite3.Error as e:
                print(f"Migration failed at {filename}: {e}")
                raise
        print("Migrations applied successfully.")
    finally:
        conn.close()

# PUBLIC_INTERFACE
def status() -> None:
    """Print applied and pending migrations."""
    db_path = get_db_path()
    print(f"Database: {db_path}")
    conn = _connect(db_path)
    try:
        _ensure_migrations_table(conn)
        applied = [fn for fn, _ in _applied_migrations(conn)]
        all_files = [os.path.basename(p) for p in _list_migration_files()]
        pending = [f for f in all_files if f not in applied]

        print("\nApplied migrations:")
        if applied:
            for a in applied:
                print(f"  ✓ {a}")
        else:
            print("  (none)")

        print("\nPending migrations:")
        if pending:
            for p in pending:
                print(f"  • {p}")
        else:
            print("  (none)")
    finally:
        conn.close()

# PUBLIC_INTERFACE
def reset() -> None:
    """Dangerous: Delete the database file and re-run migrations. Intended for local development only."""
    db_path = get_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted database at {db_path}")
    else:
        print(f"No database found at {db_path}, nothing to delete.")
    migrate()

def _print_help() -> None:
    print(
        "Usage: db_migrate.py [command]\n"
        "Commands:\n"
        "  migrate   Apply all pending migrations\n"
        "  status    Show applied and pending migrations\n"
        "  reset     Delete DB and re-run migrations (local/dev only)\n"
        "\nEnvironment:\n"
        "  SQLITE_DB: Path to SQLite DB file. Defaults to ./myapp.db if not set.\n"
    )

def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "migrate"
    if cmd == "migrate":
        migrate()
    elif cmd == "status":
        status()
    elif cmd == "reset":
        reset()
    else:
        _print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
