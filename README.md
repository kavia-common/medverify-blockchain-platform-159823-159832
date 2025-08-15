# medverify-blockchain-platform-159823-159832

Database (SQLite) initialization
- Container: medical_prescription_database
- Env var required: SQLITE_DB (path to SQLite file). See medical_prescription_database/.env.example

Quick start:
1) cd medical_prescription_database
2) (optional) export SQLITE_DB="$(pwd)/myapp.db"
3) python3 init_db.py
4) python3 test_db.py
5) Run interactive shell: python3 db_shell.py

Migrations:
- python3 db_migrate.py status
- python3 db_migrate.py migrate
- (dev only) python3 db_migrate.py reset