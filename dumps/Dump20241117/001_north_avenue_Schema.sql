-- To run migration in the command line: mysql -u root -p north_avenue < north_avenue_Schema.sql

CREATE TABLE Color (
    color_name VARCHAR(255) NOT NULL,
    PRIMARY KEY (color_name)
);

CREATE TABLE VehicleType (
    vehicle_type VARCHAR(255) NOT NULL,
    PRIMARY KEY (vehicle_type)
);

CREATE TABLE VehicleManufacturer (
    manufacturer_name VARCHAR(255) NOT NULL,
    PRIMARY KEY (manufacturer_name)
);

CREATE TABLE Vehicle (
    vehicle_identification_number VARCHAR(255) NOT NULL,
    vehicle_type VARCHAR(255) NOT NULL,
    manufacturer_name VARCHAR(255) NOT NULL,
    `condition` ENUM('Excellent', 'Very Good', 'Good', 'Fair') NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    `year` INT NOT NULL,
    fuel_type ENUM('Gas', 'Diesel', 'Natural Gas', 'Hybrid', 'Plugin Hybrid', 'Battery', 'Fuel Cell') NOT NULL,
    horsepower INT NOT NULL,
    description TEXT,
    PRIMARY KEY (vehicle_identification_number)
);

CREATE TABLE VehicleColor (
    color_name VARCHAR(255) NOT NULL,
    vehicle_identification_number VARCHAR(255) NOT NULL,
    PRIMARY KEY (color_name, vehicle_identification_number)
);

CREATE TABLE Vendor (
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(255) NOT NULL,
    address_street VARCHAR(255) NOT NULL,
    address_city VARCHAR(255) NOT NULL,
    address_state VARCHAR(255) NOT NULL,
    address_postal_code VARCHAR(255) NOT NULL,
    PRIMARY KEY (name)
);

CREATE TABLE PartsOrder (
    vehicle_identification_number VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    order_number VARCHAR(255) UNIQUE NOT NULL,
    total_cost FLOAT NOT NULL,
    PRIMARY KEY (order_number, name, vehicle_identification_number)
);

CREATE TABLE Part (
    order_number VARCHAR(255) NOT NULL,
    vendor_parts_number VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    status ENUM('Ordered', 'Received', 'Installed') NOT NULL,
    unit_price FLOAT NOT NULL,
    PRIMARY KEY (vendor_parts_number, order_number)
);

CREATE TABLE Customer (
    id INT AUTO_INCREMENT NOT NULL,
    email VARCHAR(255),
    phone_number VARCHAR(255) NOT NULL,
    address_street VARCHAR(255) NOT NULL,
    address_city VARCHAR(255) NOT NULL,
    address_state VARCHAR(255) NOT NULL,
    address_postal_code VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE BusinessCustomer (
    customer_id INT NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    tax_identification_number VARCHAR(255) NOT NULL,
    primary_contact_first_name VARCHAR(255) NOT NULL,
    primary_contact_last_name VARCHAR(255) NOT NULL,
    primary_contact_title VARCHAR(255) NOT NULL,
    PRIMARY KEY (tax_identification_number)
);

CREATE TABLE IndividualCustomer (
    customer_id INT NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    social_security_number VARCHAR(255) NOT NULL,
    PRIMARY KEY (social_security_number)
);

CREATE TABLE `User` (
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    PRIMARY KEY (username)
);

CREATE TABLE SaleTransaction (
    vehicle_identification_number VARCHAR(255) NOT NULL,
    customer_id INT NOT NULL,
    username VARCHAR(255) NOT NULL,
    sold_on DATE NOT NULL,
    sale_price FLOAT NOT NULL,
    PRIMARY KEY (vehicle_identification_number, username, customer_id)
);

CREATE TABLE PurchaseTransaction (
    vehicle_identification_number VARCHAR(255) NOT NULL,
    customer_id INT NOT NULL,
    username VARCHAR(255) NOT NULL,
    purchase_price FLOAT NOT NULL,
    purchased_on DATE NOT NULL,
    PRIMARY KEY (vehicle_identification_number, username, customer_id)
);

ALTER TABLE VehicleColor
    ADD CONSTRAINT fk_VehicleColor_colorname_Color_colorname FOREIGN KEY (color_name)
    REFERENCES Color (color_name);

ALTER TABLE VehicleColor
    ADD CONSTRAINT fk_VehicleColor_vin_Vehicle_vin FOREIGN KEY (vehicle_identification_number)
    REFERENCES Vehicle (vehicle_identification_number);

ALTER TABLE Vehicle
    ADD CONSTRAINT fk_Vehicle_vehicletype_VehicleType_vehicletype FOREIGN KEY (vehicle_type)
    REFERENCES VehicleType (vehicle_type);

ALTER TABLE Vehicle
    ADD CONSTRAINT fk_Vehicle_manufacturername_Manufacturer_manufacturername FOREIGN KEY (manufacturer_name)
    REFERENCES VehicleManufacturer (manufacturer_name);

ALTER TABLE PartsOrder
    ADD CONSTRAINT fk_PartsOrder_vin_Vehicle_vin FOREIGN KEY (vehicle_identification_number)
    REFERENCES Vehicle (vehicle_identification_number);

ALTER TABLE PartsOrder
    ADD CONSTRAINT fk_PartsOrder_name_Vendor_name FOREIGN KEY (name)
    REFERENCES Vendor (name);

ALTER TABLE Part
    ADD CONSTRAINT fk_Part_ordernumber_PartsOrder_ordernumber FOREIGN KEY (order_number)
    REFERENCES PartsOrder (order_number);

ALTER TABLE SaleTransaction
    ADD CONSTRAINT fk_SalesTransaction_vin_Vehicle_vin FOREIGN KEY (vehicle_identification_number)
    REFERENCES Vehicle (vehicle_identification_number);

ALTER TABLE SaleTransaction
    ADD CONSTRAINT fk_SalesTransaction_username_User_username FOREIGN KEY (username)
    REFERENCES `User` (username);

ALTER TABLE SaleTransaction
    ADD CONSTRAINT fk_SalesTransaction_CustomerId_customer_customerid FOREIGN KEY (customer_id)
    REFERENCES Customer (id);

ALTER TABLE PurchaseTransaction
    ADD CONSTRAINT fk_PurchaseTransaction_vin_Vehicle_vin FOREIGN KEY (vehicle_identification_number)
    REFERENCES Vehicle (vehicle_identification_number);

ALTER TABLE PurchaseTransaction
    ADD CONSTRAINT fk_PurchaseTransaction_username_User_username FOREIGN KEY (username)
    REFERENCES `User` (username);

ALTER TABLE PurchaseTransaction
    ADD CONSTRAINT fk_PurchaseTransaction_customerid_Customer_customerid FOREIGN KEY (customer_id)
    REFERENCES Customer (id);

ALTER TABLE BusinessCustomer
    ADD CONSTRAINT fk_BusinessCustomer_customerid_Customer_customerid FOREIGN KEY (customer_id)
    REFERENCES Customer (id);

ALTER TABLE IndividualCustomer
    ADD CONSTRAINT fk_IndividualCustomer_customerid_Customer_customerid FOREIGN KEY (customer_id)
    REFERENCES Customer (id);
