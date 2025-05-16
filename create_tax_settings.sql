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

-- Insert default tax settings if tax_settings table is empty
INSERT IGNORE INTO tax_settings (business_name, gstin, pan, tax_period, financial_year_start, gst_filing_due_date) VALUES
('KK Enterprises', '27AADCK1234P1ZV', 'AADCK1234P', 'Monthly', '2025-04-01', 20); 