CREATE DATABASE `bookstore`;

USE `bookstore`;

CREATE TABLE `accounts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userid` varchar(20) NOT NULL,
  `password` varchar(20) NOT NULL,
  `email` varchar(20) DEFAULT NULL,
  `user_type` int DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `inventory` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bookname` varchar(255) NOT NULL,
  `genre` varchar(20) NOT NULL,
  `available` int NOT NULL,
  `cost` decimal(9,2) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `custom` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `userid` int DEFAULT NULL,
  `bookid` int DEFAULT NULL,
  `isactive` tinyint(1) DEFAULT NULL,
  `qty` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `userid` (`userid`),
  KEY `bookid` (`bookid`),
  CONSTRAINT `custom_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `accounts` (`id`),
  CONSTRAINT `custom_ibfk_2` FOREIGN KEY (`bookid`) REFERENCES `inventory` (`id`)
);

CREATE TABLE `orderdetails` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userid` int NOT NULL,
  `orderid` int NOT NULL,
  `bookid` int NOT NULL,
  `cost` decimal(9,2) NOT NULL,
  `qty` int NOT NULL,
  `total` decimal(9,2) NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `totalamount` decimal(9,2) NOT NULL,
  `userid` int NOT NULL,
  `saledate` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
);

INSERT INTO `bookstore`.`inventory`
(`bookname`,`genre`,`available`,`cost`)
VALUES
('Harry Potter','Drama',100,99);

INSERT INTO `bookstore`.`inventory`
(`bookname`,`genre`,`available`,`cost`)
VALUES
('Kindred','Sci-Fi',50,49);
