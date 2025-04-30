-- Add role column to users table
ALTER TABLE users ADD COLUMN role ENUM('admin', 'accountant', 'viewer') NOT NULL DEFAULT 'viewer';

-- Update existing users to have admin role (you may want to change this based on your needs)
UPDATE users SET role = 'admin' WHERE id = 1; 