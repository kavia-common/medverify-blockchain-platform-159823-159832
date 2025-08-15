#!/usr/bin/env python3
"""Test SQLite database and schema presence.

This script verifies:
- The SQLite database is present and accessible
- Core tables exist after migrations
"""

import os
import sys
import sqlite3

DB_PATH = os.getenv("SQLITE_DB", "myapp.db")
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

def table_exists(cursor, name: str) -> bool:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    )
    return cursor.fetchone() is not None

def main():
    try:
        if not os.path.exists(DB_PATH):
            print(f"Database file '{DB_PATH}' not found")
            sys.exit(1)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")

        cur.execute("SELECT sqlite_version()")
        version = cur.fetchone()[0]
        print(f"SQLite version: {version}")

        missing = [t for t in REQUIRED_TABLES if not table_exists(cur, t)]
        if missing:
            print("Missing required tables:", ", ".join(sorted(missing)))
            sys.exit(2)
        else:
            print("All required tables are present.")
            sys.exit(0)

    except sqlite3.Error as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
