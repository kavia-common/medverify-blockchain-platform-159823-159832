-- 0002_seed_roles.sql
INSERT OR IGNORE INTO roles (name, description) VALUES
  ('admin', 'Platform administrator'),
  ('doctor', 'Licensed medical practitioner who can issue prescriptions'),
  ('pharmacist', 'Licensed pharmacist who can dispense and verify'),
  ('patient', 'Recipient of medical prescriptions');
