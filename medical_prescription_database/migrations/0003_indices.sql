-- 0003_indices.sql

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_public_id ON users(public_id);

-- User roles
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);

-- Prescriptions
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_doctor ON prescriptions(doctor_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_pharmacist ON prescriptions(pharmacist_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_status ON prescriptions(status);
CREATE INDEX IF NOT EXISTS idx_prescriptions_issue_date ON prescriptions(issue_date);

-- Blockchain refs
CREATE INDEX IF NOT EXISTS idx_chain_refs_prescription ON prescription_blockchain_refs(prescription_id);
CREATE INDEX IF NOT EXISTS idx_chain_refs_status ON prescription_blockchain_refs(status);

-- Audit logs
CREATE INDEX IF NOT EXISTS idx_audit_prescription ON prescription_audit_logs(prescription_id);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON prescription_audit_logs(actor_user_id);

-- Metadata
CREATE INDEX IF NOT EXISTS idx_metadata_prescription ON prescription_metadata(prescription_id);
