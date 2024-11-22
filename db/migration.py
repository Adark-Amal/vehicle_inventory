import csv
import os
from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = "mysql+pymysql://root:password098@localhost:3306/north_avenue"
engine = create_engine(DATABASE_URL)


# Helper function to execute SQL queries
def execute_query(query, params=None):
    with engine.connect() as conn:
        if params:
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))
        return result.fetchall() if result.returns_rows else None


def execute_sql_file(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return

    with open(file_path, "r") as file:
        sql_content = file.read()

    # Split by semicolon to handle multiple SQL statements
    sql_statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    for statement in sql_statements:
        try:
            print(f"Executing: {statement[:50]}...")  # Log the first 50 chars
            execute_query(statement)
        except Exception as e:
            print(f"Error executing statement: {statement[:50]}...\n{e}")


print("Loading migrations...")
execute_sql_file("../dumps/Dump20241117/001_north_avenue_Schema.sql")
execute_sql_file("../dumps/Dump20241117/002_north_avenue_Color.sql")
execute_sql_file("../dumps/Dump20241117/003_north_avenue_VehicleManufacturer.sql")
execute_sql_file("../dumps/Dump20241117/004_north_avenue_VehicleType.sql")
execute_sql_file(
    "../dumps/Dump20241117/005_north_avenue_AddUniquenessConstraintOnCustomerId.sql"
)
execute_sql_file("../dumps/Dump20241117/006_north_avenue_ChangeEmailToNullable.sql")

# Clear existing data
tables = [
    "Part",
    "PartsOrder",
    "PurchaseTransaction",
    "SaleTransaction",
    "VehicleColor",
    "Vehicle",
    "BusinessCustomer",
    "IndividualCustomer",
    "Customer",
    "User",
    "Vendor",
]

if len(tables) > 0:
    for table in tables:
        execute_query(f"DELETE FROM `{table}`")
else:
    pass

# Load Customers
with open("../dumps/DemoData/customers.tsv") as file:
    reader = csv.DictReader(file, delimiter="\t")
    for row in reader:
        # Insert into Customer
        customer_query = """
        INSERT INTO `Customer` (email, phone_number, address_street, address_city, address_state, address_postal_code)
        VALUES (:email, :phone, :street, :city, :state, :postal)
        """

        result = execute_query(
            customer_query,
            {
                "email": row["email"],
                "phone": row["phone"],
                "street": row["street"],
                "city": row["city"],
                "state": row["state"],
                "postal": row["postal"],
            },
        )

        customer_id = engine.execute("SELECT LAST_INSERT_ID()").scalar()

        # Insert into IndividualCustomer or BusinessCustomer
        if row["customer_type"] == "person":
            individual_query = """
            INSERT INTO `IndividualCustomer` (social_security_number, first_name, last_name, customer_id)
            VALUES (:ssn, :first_name, :last_name, :customer_id)
            """
            execute_query(
                individual_query,
                {
                    "ssn": row["person_ssn"],
                    "first_name": row["person_first"],
                    "last_name": row["person_last"],
                    "customer_id": customer_id,
                },
            )
        elif row["customer_type"] == "business":
            business_query = """
            INSERT INTO `BusinessCustomer` (tax_identification_number, business_name, primary_contact_first_name,
                                            primary_contact_last_name, primary_contact_title, customer_id)
            VALUES (:tax_id, :biz_name, :contact_first, :contact_last, :title, :customer_id)
            """
            execute_query(
                business_query,
                {
                    "tax_id": row["biz_tax_id"],
                    "biz_name": row["biz_name"],
                    "contact_first": row["biz_contact_first"],
                    "contact_last": row["biz_contact_last"],
                    "title": row["biz_contact_title"],
                    "customer_id": customer_id,
                },
            )

# Load Users
with open("../dumps/DemoData/users.tsv") as file:
    reader = csv.DictReader(file, delimiter="\t")
    for row in reader:
        user_query = """
        INSERT INTO `User` (username, password, first_name, last_name, role)
        VALUES (:username, :password, :first_name, :last_name, :role)
        """
        execute_query(
            user_query,
            {
                "username": row["username"],
                "password": row["password"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "role": row["role"].capitalize(),
            },
        )
        execute_query(
            "UPDATE `User` SET role = :role WHERE username='owner'", {"role": "Owner"}
        )

# Load Vendors
with open("../dumps/DemoData/vendors.tsv") as file:
    reader = csv.DictReader(file, delimiter="\t")
    for row in reader:
        vendor_query = """
        INSERT INTO `Vendor` (name, phone_number, address_street, address_city, address_state, address_postal_code)
        VALUES (:name, :phone, :street, :city, :state, :postal)
        """
        execute_query(
            vendor_query,
            {
                "name": row["vendor_name"],
                "phone": row["phone"],
                "street": row["street"],
                "city": row["city"],
                "state": row["state"],
                "postal": row["postal_code"],
            },
        )

# Load Vehicles and Related Data
with open("../dumps/DemoData/vehicles.tsv") as file:
    reader = csv.DictReader(file, delimiter="\t")
    for row in reader:
        # Insert Vehicle
        vehicle_query = """
        INSERT INTO `Vehicle` (vehicle_identification_number, vehicle_type, `condition`, manufacturer_name, 
                               model_name, `year`, fuel_type, horsepower, description)
        VALUES (:vin, :type, :condition, :manufacturer, :model, :year, :fuel, :hp, :desc)
        """
        execute_query(
            vehicle_query,
            {
                "vin": row["VIN"],
                "type": row["vehicle_type"],
                "condition": row["condition"],
                "manufacturer": row["manufacturer_name"],
                "model": row["model_name"],
                "year": row["year"],
                "fuel": row["fuel_type"],
                "hp": row["horsepower"],
                "desc": row["description"],
            },
        )

        # Insert PurchaseTransaction
        purchase_query = """
        INSERT INTO `PurchaseTransaction` (vehicle_identification_number, username, customer_id, purchase_price, purchased_on)
        VALUES (:vin, :clerk, :customer_id, :price, :purchased_on)
        """
        customer_query = """
        SELECT id FROM `Customer` c
        LEFT JOIN `IndividualCustomer` ic ON c.id = ic.customer_id 
        LEFT JOIN `BusinessCustomer` bc ON c.id = bc.customer_id
        WHERE ic.social_security_number = :customer_id OR bc.tax_identification_number = :customer_id
        """

        seller_id = execute_query(
            customer_query, {"customer_id": row["purchased_from_customer"]}
        )[0][0]
        execute_query(
            purchase_query,
            {
                "vin": row["VIN"],
                "clerk": row["purchase_clerk"],
                "customer_id": seller_id,
                "price": row["price"],
                "purchased_on": row["purchase_date"],
            },
        )

        # Insert Vehicle Colors
        for color in row["colors"].split(","):
            color_query = """
            INSERT INTO `VehicleColor` (vehicle_identification_number, color_name)
            VALUES (:vin, :color)
            """
            execute_query(color_query, {"vin": row["VIN"], "color": color})

        # Insert SaleTransaction if applicable
        if row["sale_date"]:
            sale_query = """
            INSERT INTO `SaleTransaction` (vehicle_identification_number, username, customer_id, sale_price, sold_on)
            VALUES (:vin, :salesperson, :customer_id, :price, :sold_on)
            """
            buyer_id = execute_query(
                customer_query, {"customer_id": row["sold_to_customer"]}
            )[0][0]
            execute_query(
                sale_query,
                {
                    "vin": row["VIN"],
                    "salesperson": row["salesperson"],
                    "customer_id": buyer_id,
                    "price": row["price"],
                    "sold_on": row["sale_date"],
                },
            )

# Load Parts and PartsOrder
with open("../dumps/DemoData/parts.tsv") as file:
    reader = csv.DictReader(file, delimiter="\t")
    order_numbers = set()
    for row in reader:
        order_number = f"{row['VIN']}-{row['order_num']}"

        if order_number not in order_numbers:
            parts_order_query = """
            INSERT INTO `PartsOrder` (vehicle_identification_number, order_number, name, total_cost)
            VALUES (:vin, :order_number, :name, :cost)
            """
            execute_query(
                parts_order_query,
                {
                    "vin": row["VIN"],
                    "order_number": order_number,
                    "name": row["vendor_name"],
                    "cost": 0.00,
                },
            )
            order_numbers.add(order_number)

        parts_query = """
        INSERT INTO `Part` (vendor_parts_number, order_number, unit_price, quantity, status, description)
        VALUES (:part_number, :order_number, :unit_price, :quantity, :status, :description)
        """
        execute_query(
            parts_query,
            {
                "part_number": row["part_number"],
                "order_number": order_number,
                "unit_price": row["price"],
                "quantity": row["qty"],
                "status": row["status"].capitalize(),
                "description": row["description"],
            },
        )

        # Update total cost
        total_cost_query = """
        UPDATE `PartsOrder` 
        SET total_cost = total_cost + :cost 
        WHERE order_number = :order_number
        """
        execute_query(
            total_cost_query,
            {
                "cost": float(row["price"]) * int(row["qty"]),
                "order_number": order_number,
            },
        )
