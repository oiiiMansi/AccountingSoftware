-- MySQL dump 10.13  Distrib 9.2.0, for Win64 (x86_64)
--
-- Host: localhost    Database: accounting
-- ------------------------------------------------------
-- Server version	9.2.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `billed_purchases`
--

DROP TABLE IF EXISTS `billed_purchases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `billed_purchases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vendor_name` varchar(255) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `paid_amount` decimal(10,2) DEFAULT '0.00',
  `quantity` int DEFAULT '1',
  `payment_type` enum('Cash','Credit') DEFAULT 'Cash',
  `payment_status` enum('Pending','Partially Paid','Paid') DEFAULT 'Paid',
  `gst_type` enum('CGST_SGST','IGST') DEFAULT 'CGST_SGST',
  `gst_percentage` decimal(5,2) DEFAULT '18.00',
  `date` date NOT NULL,
  `description` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `billed_purchases`
--

LOCK TABLES `billed_purchases` WRITE;
/*!40000 ALTER TABLE `billed_purchases` DISABLE KEYS */;
INSERT INTO `billed_purchases` VALUES (6,'Priya Nehra',10000.00,10000.00,2,'Cash','Paid','CGST_SGST',18.00,'2025-04-16','','2025-04-16 07:17:17'),(7,'Priya Nehra',100.00,100.00,1,'Cash','Paid','CGST_SGST',18.00,'2025-04-20','','2025-04-20 02:52:36'),(8,'roxuu',1000000.00,1000000.00,1,'Cash','Paid','CGST_SGST',18.00,'2025-04-23','','2025-04-23 08:19:00'),(9,'cre',10000.00,10000.00,1,'Cash','Paid','CGST_SGST',18.00,'2025-05-09','','2025-05-09 09:28:45');
/*!40000 ALTER TABLE `billed_purchases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bills`
--

DROP TABLE IF EXISTS `bills`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bills` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_name` varchar(255) DEFAULT NULL,
  `amount` decimal(10,2) DEFAULT NULL,
  `date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `customer_number` varchar(50) DEFAULT NULL,
  `customer_address` text,
  `shipping_address` text,
  `basic_amount` decimal(10,2) DEFAULT NULL,
  `quantity` int DEFAULT '1',
  `payment_type` enum('Cash','Credit') DEFAULT 'Cash',
  `payment_status` enum('Pending','Partially Paid','Paid') DEFAULT 'Paid',
  `gst_type` varchar(20) DEFAULT NULL,
  `gst_percentage` decimal(5,2) DEFAULT NULL,
  `gst_amount` decimal(10,2) DEFAULT NULL,
  `total_amount` decimal(10,2) DEFAULT NULL,
  `paid_amount` decimal(10,2) DEFAULT '0.00',
  `payment_date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bills`
--

LOCK TABLES `bills` WRITE;
/*!40000 ALTER TABLE `bills` DISABLE KEYS */;
INSERT INTO `bills` VALUES (10,'roxuu',NULL,'2025-04-15 18:30:00','7488379237','rgerggeg','gegerg',100.00,1,'Cash','Paid','CGST_SGST',18.00,18.00,118.00,118.00,NULL),(11,'roxuu',NULL,'2025-04-16 18:30:00','roxuu','400','kk',400.00,1,'Cash','Paid','CGST_SGST',18.00,72.00,472.00,472.00,NULL),(28,'a',NULL,'2025-05-08 18:30:00','7488379237','aaaa','aaaa',1000000.00,1,'Credit','Partially Paid','CGST_SGST',18.00,180000.00,1180000.00,70000.00,NULL),(29,'Shyam',NULL,'2025-05-09 09:39:46','7488379237','sdad','ads',120000.00,1,'Cash','Paid','CGST_SGST',18.00,21600.00,141600.00,0.00,NULL);
/*!40000 ALTER TABLE `bills` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `budget`
--

DROP TABLE IF EXISTS `budget`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `budget` (
  `id` int NOT NULL AUTO_INCREMENT,
  `year` int NOT NULL,
  `account_name` varchar(100) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `version` enum('Actual','Budget','Forecast') DEFAULT 'Budget',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `budget`
--

LOCK TABLES `budget` WRITE;
/*!40000 ALTER TABLE `budget` DISABLE KEYS */;
/*!40000 ALTER TABLE `budget` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `budget_planning`
--

DROP TABLE IF EXISTS `budget_planning`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `budget_planning` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account_id` int DEFAULT NULL,
  `year` varchar(10) DEFAULT NULL,
  `version` varchar(50) DEFAULT NULL,
  `amount` decimal(12,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `budget_planning`
--

LOCK TABLES `budget_planning` WRITE;
/*!40000 ALTER TABLE `budget_planning` DISABLE KEYS */;
/*!40000 ALTER TABLE `budget_planning` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `employee_targets`
--

DROP TABLE IF EXISTS `employee_targets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employee_targets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `target_per_year` int DEFAULT NULL,
  `target_per_month` int DEFAULT NULL,
  `achieved_target_year` int DEFAULT NULL,
  `achieved_target_month` int DEFAULT NULL,
  `percentage_achieved` float DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employee_targets`
--

LOCK TABLES `employee_targets` WRITE;
/*!40000 ALTER TABLE `employee_targets` DISABLE KEYS */;
/*!40000 ALTER TABLE `employee_targets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `employees`
--

DROP TABLE IF EXISTS `employees`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employees` (
  `id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `dob` date DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `department` varchar(50) DEFAULT NULL,
  `position` varchar(50) DEFAULT NULL,
  `joining_date` date DEFAULT NULL,
  `salary` decimal(10,2) DEFAULT NULL,
  `address` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employees`
--

LOCK TABLES `employees` WRITE;
/*!40000 ALTER TABLE `employees` DISABLE KEYS */;
/*!40000 ALTER TABLE `employees` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `expenses`
--

DROP TABLE IF EXISTS `expenses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expenses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `expense_name` varchar(255) DEFAULT NULL,
  `amount` decimal(10,2) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `gst` decimal(10,2) DEFAULT '0.00',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expenses`
--

LOCK TABLES `expenses` WRITE;
/*!40000 ALTER TABLE `expenses` DISABLE KEYS */;
INSERT INTO `expenses` VALUES (2,'samosa',355.00,'Other','2025-05-01 18:30:00',63.90);
/*!40000 ALTER TABLE `expenses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leads`
--

DROP TABLE IF EXISTS `leads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leads` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `contact` varchar(100) NOT NULL,
  `company` varchar(100) DEFAULT NULL,
  `source` varchar(100) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `assigned_to` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leads`
--

LOCK TABLES `leads` WRITE;
/*!40000 ALTER TABLE `leads` DISABLE KEYS */;
INSERT INTO `leads` VALUES (1,'Akshita Sharma','7014778141','APM tech ','website','New','mansi saini ','2025-04-06 16:36:01');
/*!40000 ALTER TABLE `leads` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `non_billed_sales`
--

DROP TABLE IF EXISTS `non_billed_sales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `non_billed_sales` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_name` varchar(255) NOT NULL,
  `contact_number` varchar(50) DEFAULT NULL,
  `item_details` text,
  `quantity` int DEFAULT '1',
  `amount` decimal(10,2) NOT NULL,
  `paid_amount` decimal(10,2) DEFAULT '0.00',
  `payment_type` enum('Cash','Credit') DEFAULT 'Cash',
  `payment_status` enum('Pending','Partially Paid','Paid') DEFAULT 'Paid',
  `date` date NOT NULL,
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `payment_date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `non_billed_sales`
--

LOCK TABLES `non_billed_sales` WRITE;
/*!40000 ALTER TABLE `non_billed_sales` DISABLE KEYS */;
INSERT INTO `non_billed_sales` VALUES (3,'Shyam','7896541236','cello bottle',1,601.00,601.00,'Cash','Paid','2025-04-15','','2025-04-16 07:36:33',NULL),(4,'asd','5484874546','nothing',1,10233.00,10233.00,'Cash','Paid','2025-04-19','','2025-04-19 08:45:12',NULL);
/*!40000 ALTER TABLE `non_billed_sales` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchases`
--

DROP TABLE IF EXISTS `purchases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vendor_name` varchar(255) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `paid_amount` decimal(10,2) DEFAULT '0.00',
  `quantity` int DEFAULT '1',
  `payment_type` enum('Cash','Credit') DEFAULT 'Cash',
  `payment_status` enum('Pending','Partially Paid','Paid') DEFAULT 'Paid',
  `date` date NOT NULL,
  `item_details` text NOT NULL,
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchases`
--

LOCK TABLES `purchases` WRITE;
/*!40000 ALTER TABLE `purchases` DISABLE KEYS */;
INSERT INTO `purchases` VALUES (3,'Raam',300.00,300.00,1,'Cash','Paid','2025-04-01','Cello Bottle','','2025-04-16 07:31:34'),(4,'roxuu',350.00,350.00,7,'Cash','Paid','2025-04-17','ii','ii','2025-04-17 09:00:47'),(5,'roxuu',10000.00,10000.00,1,'Cash','Paid','2025-04-24','xasx','axsax','2025-04-23 08:14:25');
/*!40000 ALTER TABLE `purchases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `revenue`
--

DROP TABLE IF EXISTS `revenue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `revenue` (
  `id` int NOT NULL AUTO_INCREMENT,
  `source` varchar(255) DEFAULT NULL,
  `amount` decimal(10,2) DEFAULT NULL,
  `date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `revenue`
--

LOCK TABLES `revenue` WRITE;
/*!40000 ALTER TABLE `revenue` DISABLE KEYS */;
INSERT INTO `revenue` VALUES (1,'saling',40000.00,'2025-04-08');
/*!40000 ALTER TABLE `revenue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `salary`
--

DROP TABLE IF EXISTS `salary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `salary` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_name` varchar(255) DEFAULT NULL,
  `amount` decimal(10,2) DEFAULT NULL,
  `date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `salary`
--

LOCK TABLES `salary` WRITE;
/*!40000 ALTER TABLE `salary` DISABLE KEYS */;
INSERT INTO `salary` VALUES (3,'asd',10000.00,'2025-04-17');
/*!40000 ALTER TABLE `salary` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock`
--

DROP TABLE IF EXISTS `stock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_name` varchar(255) NOT NULL,
  `quantity` int NOT NULL,
  `added_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock`
--

LOCK TABLES `stock` WRITE;
/*!40000 ALTER TABLE `stock` DISABLE KEYS */;
INSERT INTO `stock` VALUES (4,'cello bottle',1,'2025-04-16 07:30:39');
/*!40000 ALTER TABLE `stock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `description` varchar(255) NOT NULL,
  `transaction_type` enum('credit','debit') NOT NULL DEFAULT 'credit',
  `reference_id` int DEFAULT NULL,
  `reference_type` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `payment_note` text,
  `narration` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transactions`
--

LOCK TABLES `transactions` WRITE;
/*!40000 ALTER TABLE `transactions` DISABLE KEYS */;
INSERT INTO `transactions` VALUES (12,'2025-04-16 00:00:00',300.00,'Purchase from Ram: Cello Bottle','debit',3,'purchase','2025-04-16 07:31:34',NULL,NULL),(13,'2025-04-15 00:00:00',600.00,'Sale to Shyam: cello bottle','credit',3,'non_billed_sale','2025-04-16 07:36:33',NULL,NULL),(14,'2025-04-17 00:00:00',472.00,'Bill to roxuu','credit',11,'bill','2025-04-17 08:40:57',NULL,NULL),(17,'2025-04-19 00:00:00',10233.00,'Sale to asd: nothing (Qty: 1)','credit',4,'non_billed_sale','2025-04-19 08:45:12',NULL,NULL),(18,'2025-04-20 00:00:00',118.00,'Purchase from Priya Nehra:  (Qty: 1)','debit',7,'billed_purchase','2025-04-20 02:52:36',NULL,NULL),(29,'2025-05-09 00:00:00',70000.00,'Partial payment for bill #28','credit',28,'bill_payment','2025-05-09 09:21:51',NULL,NULL),(30,'2025-05-09 00:00:00',11800.00,'Purchase from cre:  (Qty: 1)','debit',9,'billed_purchase','2025-05-09 09:28:45',NULL,NULL),(31,'2025-05-09 00:00:00',5000.00,'Partial payment for billed purchase #9','debit',9,'billed_purchase_payment','2025-05-09 09:29:06',NULL,NULL),(32,'2025-05-09 00:00:00',5000.00,'Partial payment for billed purchase #9','debit',9,'billed_purchase_payment','2025-05-09 09:29:16',NULL,NULL),(33,'2025-05-09 15:09:46',141600.00,'Bill for Shyam','credit',29,'bill','2025-05-09 09:39:46',NULL,NULL);
/*!40000 ALTER TABLE `transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('admin','accountant','viewer') NOT NULL DEFAULT 'viewer',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','scrypt:32768:8:1$dzu8G5JuutZ5lGOU$36943b4b9b285bd77c3ed0e33595548dc5677c3550d30d71eb09e50dbadf22cffe7a7df26402b3a3eea41423a85d86ab3fcc66e4fe39d0c2ad72dcdfb4d10bd8','admin','2025-05-01 05:00:45','2025-05-01 05:54:19'),(2,'accountant','scrypt:32768:8:1$dzu8G5JuutZ5lGOU$36943b4b9b285bd77c3ed0e33595548dc5677c3550d30d71eb09e50dbadf22cffe7a7df26402b3a3eea41423a85d86ab3fcc66e4fe39d0c2ad72dcdfb4d10bd8','accountant','2025-05-01 05:00:45','2025-05-01 05:54:19'),(3,'viewer','scrypt:32768:8:1$dzu8G5JuutZ5lGOU$36943b4b9b285bd77c3ed0e33595548dc5677c3550d30d71eb09e50dbadf22cffe7a7df26402b3a3eea41423a85d86ab3fcc66e4fe39d0c2ad72dcdfb4d10bd8','viewer','2025-05-01 05:00:45','2025-05-01 05:54:19'),(4,'user','scrypt:32768:8:1$dzu8G5JuutZ5lGOU$36943b4b9b285bd77c3ed0e33595548dc5677c3550d30d71eb09e50dbadf22cffe7a7df26402b3a3eea41423a85d86ab3fcc66e4fe39d0c2ad72dcdfb4d10bd8','viewer','2025-05-01 05:02:10','2025-05-01 05:54:19'),(5,'roxanne','scrypt:32768:8:1$dzu8G5JuutZ5lGOU$36943b4b9b285bd77c3ed0e33595548dc5677c3550d30d71eb09e50dbadf22cffe7a7df26402b3a3eea41423a85d86ab3fcc66e4fe39d0c2ad72dcdfb4d10bd8','admin','2025-05-01 05:04:56','2025-05-01 05:54:19');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-05-10  8:52:07
