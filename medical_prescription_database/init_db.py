#!/usr/bin/env python3
"""Initialize the SQLite database for the medical_prescription_database.

This script:
- Resolves the database path from SQLITE_DB or defaults to ./myapp.db
- Performs a preflight schema check to ensure backward-compat columns exist (users.public_id)
- Runs all SQL migrations in ./migrations using db_migrate.py
- Writes connection details to db_connection.txt
- Generates db_visualizer/sqlite.env for the local Node.js DB viewer

Healthcare note:
If you require HL7/FHIR-aligned data structures (e.g., FHIR MedicationRequest, Patient), please let us know.
This schema uses a pragmatic structure with roles (doctor, pharmacist, patient), prescriptions, audit logs, and blockchain references.
"""

import os
import sys
import sqlite3
from datetime import datetime

# PUBLIC_INTERFACE
def get_db_path() -> str:
    """Return the path to the SQLite database file using the SQLITE_DB env var or default to 'myapp.db'."""
    return os.getenv("SQLITE_DB", "myapp.db")

# PUBLIC_INTERFACE
def write_connection_info(db_path: str) -> None:
    """Persist connection instructions for developers and other containers."""
    connection_string = f"sqlite:///{os.path.abspath(db_path)}"
    try:
        with open("db_connection.txt", "w", encoding="utf-8") as f:
            f.write("# SQLite connection methods:\n")
            f.write(f"# Python: sqlite3.connect('{db_path}')\n")
            f.write(f"# Connection string: {connection_string}\n")
            f.write(f"# File path: {os.path.abspath(db_path)}\n")
        print("✓ Connection information saved to db_connection.txt")
    except Exception as e:
        print(f"Warning: Could not save connection info: {e}")

# PUBLIC_INTERFACE
def write_visualizer_env(db_path: str) -> None:
    """Create or update db_visualizer/sqlite.env with the resolved SQLite DB path."""
    try:
        os.makedirs("db_visualizer", exist_ok=True)
        with open("db_visualizer/sqlite.env", "w", encoding="utf-8") as f:
            f.write(f'export SQLITE_DB="{os.path.abspath(db_path)}"\n')
        print("✓ Environment variables saved to db_visualizer/sqlite.env")
    except Exception as e:
        print(f"Warning: Could not save environment variables: {e}")

# PUBLIC_INTERFACE
def ensure_users_public_id_column(db_path: str) -> None:
    """Ensure users.public_id column exists (backward-compat for older databases).

    Logic:
    - Check PRAGMA table_info('users') for 'public_id'
    - If missing, temporarily disable foreign_keys for the connection (safety) and ALTER TABLE to add the column
    - Create the supporting index (IF NOT EXISTS) for performance

    This function is idempotent and safe on all SQLite versions that support ALTER TABLE ADD COLUMN.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cur.fetchall()}

        if "public_id" not in cols:
            # Disable foreign_keys for the schema change scope as a precaution
            conn.execute("PRAGMA foreign_keys = OFF")
            try:
                conn.execute("ALTER TABLE users ADD COLUMN public_id TEXT")
                print("✓ Added users.public_id column")
            finally:
                conn.execute("PRAGMA foreign_keys = ON")
            conn.commit()
        else:
            # Column exists; nothing to do
            pass

        # Create index if not exists (no-op if already present)
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_public_id ON users(public_id)")
            conn.commit()
        except sqlite3.Error as e:
            # If this fails (e.g., very old SQLite without IF NOT EXISTS on indexes),
            # it's safe to ignore because a later migration (0003_indices.sql) will create it,
            # or it may already exist.
            print(f"Note: could not create idx_users_public_id (will be handled by migrations if needed): {e}")

    except sqlite3.Error as e:
        print(f"Warning: preflight ensure_users_public_id_column failed: {e}")
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

# PUBLIC_INTERFACE
def run_migrations() -> None:
    """Run database migrations using the local migration runner."""
    from db_migrate import migrate
    migrate()

def main() -> None:
    print("Starting SQLite database initialization...")
    db_path = get_db_path()
    print(f"Resolved DB path: {db_path}")

    # Ensure parent dir exists for custom paths
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    # Preflight: ensure backward-compatible columns exist before running SQL migrations
    ensure_users_public_id_column(db_path)

    # Run migrations
    run_migrations()

    # Write helper files
    write_connection_info(db_path)
    write_visualizer_env(db_path)

    print("\nInitialization complete.")
    print(f"Database: {os.path.basename(db_path)}")
    print(f"Location: {os.path.abspath(db_path)}")
    print("\nTo use with Node.js viewer, run: source db_visualizer/sqlite.env")
    print("\nReminders:")
    print("- Ensure the backend container uses the same SQLITE_DB path via environment variables.")
    print("- For FHIR/HL7 compatible schemas, open a ticket to extend the data model accordingly.")
    print(f"- Timestamp: {datetime.utcnow().isoformat()}Z")

if __name__ == "__main__":
    main()
