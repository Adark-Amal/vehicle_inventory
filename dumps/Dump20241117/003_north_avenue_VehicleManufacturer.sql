CREATE DATABASE  IF NOT EXISTS `north_avenue` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `north_avenue`;
-- MySQL dump 10.13  Distrib 8.0.40, for macos14 (x86_64)
--
-- Host: localhost    Database: north_avenue
-- ------------------------------------------------------
-- Server version	8.0.31

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `VehicleManufacturer`
--

DROP TABLE IF EXISTS `VehicleManufacturer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `VehicleManufacturer` (
  `manufacturer_name` varchar(255) NOT NULL,
  PRIMARY KEY (`manufacturer_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `VehicleManufacturer`
--

LOCK TABLES `VehicleManufacturer` WRITE;
/*!40000 ALTER TABLE `VehicleManufacturer` DISABLE KEYS */;
INSERT INTO `VehicleManufacturer` VALUES ('Acura'),('Alfa Romeo'),('Aston Martin'),('Audi'),('Bentley'),('BMW'),('Buick'),('Cadillac'),('Chevrolet'),('Chrysler'),('Dodge'),('Ferrari'),('FIAT'),('Ford'),('Geeley'),('Genesis'),('GMC'),('Honda'),('Hyundai'),('INFINITI'),('Jaguar'),('Jeep'),('Karma'),('Kia'),('Lamborghini'),('Land Rover'),('Lexus'),('Lincoln'),('Lotus'),('Maserati'),('MAZDA'),('McLaren'),('Mercedes-Benz'),('MINI'),('Mitsubishi'),('Nio'),('Nissan'),('Porsche'),('Ram'),('Rivian'),('Rolls-Royce'),('smart'),('Subaru'),('Tesla'),('Toyota'),('Volkswagen'),('Volvo'),('XPeng');
/*!40000 ALTER TABLE `VehicleManufacturer` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-11-17 20:39:42
