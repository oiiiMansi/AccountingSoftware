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

-- Insert default tax rates if tax_rates table is empty
INSERT IGNORE INTO tax_rates (name, type, rate, description, is_active, effective_from) VALUES
('GST 5%', 'GST', 5.00, 'GST at 5% rate', 1, '2025-01-01'),
('GST 12%', 'GST', 12.00, 'GST at 12% rate', 1, '2025-01-01'),
('GST 18%', 'GST', 18.00, 'GST at 18% rate', 1, '2025-01-01'),
('GST 28%', 'GST', 28.00, 'GST at 28% rate', 1, '2025-01-01'),
('CGST 9%', 'CGST', 9.00, 'Central GST component at 9%', 1, '2025-01-01'),
('SGST 9%', 'SGST', 9.00, 'State GST component at 9%', 1, '2025-01-01'),
('IGST 18%', 'IGST', 18.00, 'Integrated GST at 18%', 1, '2025-01-01'); 