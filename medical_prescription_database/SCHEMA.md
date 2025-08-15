Medical Prescription Database Schema (SQLite)

Overview
This schema supports a blockchain-enabled medical prescription platform. It includes:
- Users and roles (doctor, pharmacist, patient, admin)
- Prescriptions, lifecycle status, and relationships to users
- Blockchain transaction references (e.g., Solana transaction signatures)
- Audit logs for change tracking and compliance
- Arbitrary metadata per prescription

Healthcare standards note
If alignment with HL7 FHIR (e.g., Patient, Practitioner, MedicationRequest resources) is required, please raise a request. This schema is pragmatic and optimized for application needs; FHIR-compatible extensions can be added.

Tables
1) roles
- id INTEGER PK
- name TEXT UNIQUE NOT NULL (admin, doctor, pharmacist, patient)
- description TEXT

2) users
- id INTEGER PK
- public_id TEXT UNIQUE (for external references, e.g., UUID)
- email TEXT UNIQUE NOT NULL
- username TEXT UNIQUE
- full_name TEXT
- password_hash TEXT
- password_algo TEXT (e.g., argon2, bcrypt)
- is_active INTEGER DEFAULT 1
- created_at TEXT DEFAULT CURRENT_TIMESTAMP
- updated_at TEXT DEFAULT CURRENT_TIMESTAMP

3) user_roles (many-to-many between users and roles)
- user_id INTEGER FK -> users.id ON DELETE CASCADE
- role_id INTEGER FK -> roles.id ON DELETE RESTRICT
- assigned_at TEXT DEFAULT CURRENT_TIMESTAMP
- PRIMARY KEY (user_id, role_id)

4) prescriptions
- id TEXT PK (UUID provided by backend)
- number TEXT UNIQUE (human-readable code)
- patient_id INTEGER FK -> users.id
- doctor_id INTEGER FK -> users.id
- pharmacist_id INTEGER FK -> users.id (nullable, set when fulfilled)
- drug_name TEXT NOT NULL
- dosage TEXT
- quantity INTEGER
- units TEXT
- frequency TEXT
- duration_days INTEGER
- instructions TEXT
- issue_date TEXT DEFAULT date('now')
- expires_at TEXT
- status TEXT DEFAULT 'DRAFT' CHECK IN ('DRAFT','ISSUED','REVOKED','FILLED','EXPIRED','VERIFIED')
- created_at TEXT DEFAULT CURRENT_TIMESTAMP
- updated_at TEXT DEFAULT CURRENT_TIMESTAMP

5) prescription_blockchain_refs
- id INTEGER PK
- prescription_id TEXT FK -> prescriptions.id ON DELETE CASCADE
- chain TEXT DEFAULT 'solana'
- network TEXT CHECK IN ('mainnet-beta','testnet','devnet','localnet')
- tx_signature TEXT UNIQUE
- account_address TEXT
- slot INTEGER
- block_time INTEGER
- status TEXT CHECK IN ('processed','confirmed','finalized')
- created_at TEXT DEFAULT CURRENT_TIMESTAMP

6) prescription_audit_logs
- id INTEGER PK
- prescription_id TEXT FK -> prescriptions.id ON DELETE CASCADE
- action TEXT (CREATED, ISSUED, UPDATED, FILLED, REVOKED, VERIFIED, EXPIRED)
- actor_user_id INTEGER FK -> users.id ON DELETE SET NULL
- actor_role TEXT
- ip_address TEXT
- user_agent TEXT
- details TEXT (JSON or free text)
- created_at TEXT DEFAULT CURRENT_TIMESTAMP

7) prescription_metadata
- id INTEGER PK
- prescription_id TEXT FK -> prescriptions.id ON DELETE CASCADE
- key TEXT NOT NULL
- value TEXT  (JSON or free text)
- created_at TEXT DEFAULT CURRENT_TIMESTAMP
- UNIQUE (prescription_id, key)

Indexes
- Users: email, public_id
- User roles: user_id, role_id
- Prescriptions: patient_id, doctor_id, pharmacist_id, status, issue_date
- Blockchain refs: prescription_id, status
- Audit logs: prescription_id, actor_user_id
- Metadata: prescription_id

Migrations
- 0001_create_schema.sql: Core tables and triggers
- 0002_seed_roles.sql: Insert default roles
- 0003_indices.sql: Performance indices

Operations
- Initialize: python init_db.py (uses SQLITE_DB if set)
- Migrate: python db_migrate.py migrate
- Status: python db_migrate.py status
- Reset (dev only): SQLITE_DB=./myapp.db python db_migrate.py reset

Environment
- SQLITE_DB: Database file path used by all scripts and services
