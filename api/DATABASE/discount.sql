CREATE Database discount if not exists;
use discount;

CREATE TABLE  ecouponrecords (
   coupon_id int(11) NOT NULL,
   coupon_name varchar(255) NOT NULL,
   consumer_name varchar(255) NOT NULL,
   consumer_number varchar(255) NOT NULL,
   consumer_email varchar(100) DEFAULT NULL,
   gender varchar(50) NOT NULL,
   discount_amount varchar(10) NOT NULL,
   coupon_code text DEFAULT NULL,
   validity_date date NOT NULL,
   identity_mark text DEFAULT NULL,
   image varchar(255) DEFAULT NULL,
   hash_code varchar(255) DEFAULT NULL
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
);


CREATE TABLE users (
    user_id int(11) NOT NULL,
    username varchar(255) NOT NULL,
    password varchar(255) NOT NULL,
    role varchar(50) DEFAULT 'user'
);
