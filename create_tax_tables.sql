-- Create tax_filing table if it doesn't exist
CREATE TABLE IF NOT EXISTS `tax_filing` (
  `id` int NOT NULL AUTO_INCREMENT,
  `filing_type` enum('GST','Income Tax','TDS','Other') NOT NULL DEFAULT 'GST',
  `period_start` date NOT NULL,
  `period_end` date NOT NULL,
  `due_date` date NOT NULL,
  `filing_date` date DEFAULT NULL,
  `status` enum('Pending','Filed','Late Filed','Under Query') NOT NULL DEFAULT 'Pending',
  `collected_amount` decimal(10,2) DEFAULT '0.00',
  `paid_amount` decimal(10,2) DEFAULT '0.00',
  `net_payable` decimal(10,2) DEFAULT '0.00',
  `reference_number` varchar(50) DEFAULT NULL,
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create tax_rates table if it doesn't exist
CREATE TABLE IF NOT EXISTS `tax_rates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `type` enum('GST','IGST','CGST','SGST','Income Tax','Other') NOT NULL DEFAULT 'GST',
  `rate` decimal(10,2) NOT NULL,
  `description` text,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `hsn_code` varchar(20) DEFAULT NULL,
  `effective_from` date NOT NULL,
  `effective_to` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_tax_name_type` (`name`, `type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create tax_settings table if it doesn't exist
CREATE TABLE IF NOT EXISTS `tax_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `business_name` varchar(255) NOT NULL,
  `gstin` varchar(20) DEFAULT NULL,
  `pan` varchar(20) DEFAULT NULL,
  `tax_period` enum('Monthly','Quarterly','Annually') NOT NULL DEFAULT 'Monthly',
  `financial_year_start` date DEFAULT NULL,
  `gst_filing_due_date` int DEFAULT '20',
  `default_tax_rate_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create tax_transactions table if it doesn't exist
CREATE TABLE IF NOT EXISTS `tax_transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transaction_type` enum('Collected','Paid','Adjustment') NOT NULL,
  `reference_id` int NOT NULL,
  `reference_type` enum('Bill','Purchase','Expense','Other') NOT NULL,
  `tax_rate_id` int DEFAULT NULL,
  `taxable_amount` decimal(10,2) NOT NULL,
  `tax_amount` decimal(10,2) NOT NULL,
  `hsn_code` varchar(20) DEFAULT NULL,
  `date` date NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert default tax rates if tax_rates table is empty
INSERT INTO tax_rates (name, type, rate, description, is_active, effective_from)
SELECT * FROM (
    SELECT 'GST 5%' as name, 'GST' as type, 5.00 as rate, 'GST at 5% rate' as description, 1 as is_active, '2025-01-01' as effective_from
    UNION SELECT 'GST 12%', 'GST', 12.00, 'GST at 12% rate', 1, '2025-01-01'
    UNION SELECT 'GST 18%', 'GST', 18.00, 'GST at 18% rate', 1, '2025-01-01'
    UNION SELECT 'GST 28%', 'GST', 28.00, 'GST at 28% rate', 1, '2025-01-01'
    UNION SELECT 'CGST 9%', 'CGST', 9.00, 'Central GST component at 9%', 1, '2025-01-01'
    UNION SELECT 'SGST 9%', 'SGST', 9.00, 'State GST component at 9%', 1, '2025-01-01'
    UNION SELECT 'IGST 18%', 'IGST', 18.00, 'Integrated GST at 18%', 1, '2025-01-01'
) as tmp
WHERE NOT EXISTS (SELECT 1 FROM tax_rates LIMIT 1);

-- Insert default tax settings if tax_settings table is empty
INSERT INTO tax_settings (business_name, gstin, pan, tax_period, financial_year_start, gst_filing_due_date, default_tax_rate_id)
SELECT * FROM (
    SELECT 'KK Enterprises' as business_name, '27AADCK1234P1ZV' as gstin, 'AADCK1234P' as pan, 
           'Monthly' as tax_period, '2025-04-01' as financial_year_start, 20 as gst_filing_due_date, 
           (SELECT id FROM tax_rates WHERE name = 'GST 18%' LIMIT 1) as default_tax_rate_id
) as tmp
WHERE NOT EXISTS (SELECT 1 FROM tax_settings LIMIT 1);

-- Add foreign key constraint to tax_settings if it doesn't exist
SET @constraint_exists = (
    SELECT COUNT(*) 
    FROM information_schema.TABLE_CONSTRAINTS 
    WHERE CONSTRAINT_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'tax_settings' 
    AND CONSTRAINT_NAME = 'fk_default_tax_rate'
);

SET @sql = IF(@constraint_exists = 0, 
    'ALTER TABLE tax_settings ADD CONSTRAINT fk_default_tax_rate FOREIGN KEY (default_tax_rate_id) REFERENCES tax_rates(id) ON DELETE SET NULL',
    'SELECT "Foreign key constraint already exists"');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add foreign key constraint to tax_transactions if it doesn't exist
SET @constraint_exists = (
    SELECT COUNT(*) 
    FROM information_schema.TABLE_CONSTRAINTS 
    WHERE CONSTRAINT_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'tax_transactions' 
    AND CONSTRAINT_NAME = 'fk_tax_rate'
);

SET @sql = IF(@constraint_exists = 0, 
    'ALTER TABLE tax_transactions ADD CONSTRAINT fk_tax_rate FOREIGN KEY (tax_rate_id) REFERENCES tax_rates(id) ON DELETE SET NULL',
    'SELECT "Foreign key constraint already exists"');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt; 