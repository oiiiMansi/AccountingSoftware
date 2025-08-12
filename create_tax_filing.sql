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