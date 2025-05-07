CREATE DATABASE discount;

USE discount;

CREATE TABLE EcouponRecords (
    coupon_id INT AUTO_INCREMENT PRIMARY KEY,
    coupon_name VARCHAR(255) NOT NULL,
    consumer_name VARCHAR(255) NOT NULL,
    consumer_number VARCHAR(255) NOT NULL,
    consumer_email VARCHAR(100),
    gender VARCHAR(50) NOT NULL,
    discount_amount VARCHAR(10) NOT NULL,
    coupon_code TEXT,
    validity_date DATE NOT NULL,
    identity_mark TEXT,
    image VARCHAR(255),
    hash_code VARCHAR(255)
);

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user'  -- role can be 'user' or 'admin'
);


CREATE TABLE products (
   product_id int(11) NOT NULL,
   product_name varchar(255) NOT NULL,
   description text DEFAULT NULL,
   price decimal(10,2) NOT NULL,
   image varchar(255) DEFAULT NULL,
   stock_quantity int(11) DEFAULT 0,
   category varchar(100) DEFAULT NULL,
   created_at timestamp NOT NULL DEFAULT current_timestamp(),
   updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
