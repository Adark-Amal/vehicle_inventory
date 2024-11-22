import pandas as pd
from sqlalchemy import text
from db.session import create_session
from typing import List, Optional, Dict
import streamlit as st


def search_vehicles(
    vehicle_type: str = None,
    manufacturer: str = None,
    year: int = None,
    fuel_type: str = None,
    color: str = None,
    keyword: str = None,
    vin: str = None,
    vehicle_status: str = None,
    role: str = "Public",
) -> pd.DataFrame:
    """
    Searches vehicles based on the provided criteria using raw SQL.

    Parameters:
        vehicle_type (str, optional): The type of vehicle (e.g., Sedan, SUV).
        manufacturer (str, optional): The vehicle manufacturer.
        year (int, optional): The manufacturing year.
        fuel_type (str, optional): The type of fuel used by the vehicle.
        color (str, optional): The color of the vehicle.
        keyword (str, optional): A keyword to search within the manufacturer, model, year, and description fields.
        vin (str, optional): Specific vehicle identification number to search for.
        vehicle_status (str, optional): Filter by vehicle status ("Sold", "Unsold").
        role (str): User role performing the search (e.g., Public, Salesperson, Manager, etc.).

    Returns:
        pd.DataFrame: DataFrame containing matching vehicle details, sorted by vehicle_identification_number.
    """
    query = """
        SELECT 
            v.vehicle_identification_number AS VIN,
            v.vehicle_type AS VehicleType,
            v.manufacturer_name AS Manufacturer,
            v.model_name AS Model,
            v.year AS Year,
            v.fuel_type AS FuelType,
            GROUP_CONCAT(DISTINCT vc.color_name SEPARATOR ', ') AS Colors,
            v.horsepower AS Horsepower,
            -- Calculate SalePrice dynamically using aggregated parts cost
            CASE
                WHEN st.sale_price IS NOT NULL THEN st.sale_price
                ELSE ROUND((1.25 * pt.purchase_price) + (1.1 * IFNULL(po_aggregated.TotalPartsCost, 0)), 2)
            END AS SalePrice,
            pt.purchase_price AS PurchasePrice,
            pt.purchased_on AS PurchaseDate,
            ROUND(COALESCE(po_aggregated.TotalPartsCost, 0), 2) AS TotalPartsCost,
            v.description AS Description
        FROM Vehicle v
        LEFT JOIN VehicleColor vc ON v.vehicle_identification_number = vc.vehicle_identification_number
        LEFT JOIN SaleTransaction st ON v.vehicle_identification_number = st.vehicle_identification_number
        LEFT JOIN PurchaseTransaction pt ON v.vehicle_identification_number = pt.vehicle_identification_number
        -- Pre-aggregate PartsOrder costs by vehicle
        LEFT JOIN (
            SELECT 
                vehicle_identification_number, 
                SUM(total_cost) AS TotalPartsCost
            FROM PartsOrder
            GROUP BY vehicle_identification_number
        ) po_aggregated ON v.vehicle_identification_number = po_aggregated.vehicle_identification_number
    """

    # Role-Based Filtering
    if role in ["Public", "Salesperson"]:
        query += """
            WHERE st.sale_price IS NULL -- Unsold vehicles only
            AND NOT EXISTS (
                SELECT 1 FROM Part p
                INNER JOIN PartsOrder po_sub ON p.order_number = po_sub.order_number
                WHERE po_sub.vehicle_identification_number = v.vehicle_identification_number
                  AND p.status != 'Installed'
            ) -- No pending parts
        """
    elif role == "Inventory clerk":
        query += "WHERE st.sale_price IS NULL"  # Show all unsold vehicles, with or without pending parts
    elif role in ["Manager", "Owner"]:
        if vehicle_status == "Sold":
            query += "WHERE st.sale_price IS NOT NULL"  # Show only sold vehicles
        elif vehicle_status == "Unsold":
            query += "WHERE st.sale_price IS NULL"  # Show only unsold vehicles
        else:
            query += "WHERE 1=1"  # Show all vehicles (default for Managers and Owners)

    # Parameters dictionary for dynamic filtering
    params = {}

    # Add filters dynamically based on input
    if vehicle_type and vehicle_type != "Any":
        query += " AND v.vehicle_type = :vehicle_type"
        params["vehicle_type"] = vehicle_type
    if manufacturer and manufacturer != "Any":
        query += " AND v.manufacturer_name = :manufacturer"
        params["manufacturer"] = manufacturer
    if year and year != "Any":
        query += " AND v.year = :year"
        params["year"] = year
    if fuel_type and fuel_type != "Any":
        query += " AND v.fuel_type = :fuel_type"
        params["fuel_type"] = fuel_type
    if color and color != "Any":
        query += " AND vc.color_name = :color"
        params["color"] = color
    if keyword:
        query += """
            AND (
                v.manufacturer_name LIKE :keyword OR
                v.model_name LIKE :keyword OR
                CAST(v.year AS CHAR) LIKE :keyword OR
                v.description LIKE :keyword
            )
        """
        params["keyword"] = f"%{keyword}%"
    if vin:
        query += " AND v.vehicle_identification_number = :vin"
        params["vin"] = vin

    query += """
    GROUP BY 
        v.vehicle_identification_number, 
        v.vehicle_type, 
        v.manufacturer_name, 
        v.model_name, 
        v.year, 
        v.fuel_type, 
        v.horsepower, 
        st.sale_price,
        pt.purchased_on, 
        pt.purchase_price,
        v.description
    ORDER BY v.vehicle_identification_number ASC
    """

    # Execute query and fetch results
    with create_session() as session:
        results = session.execute(query, params).fetchall()

    # Convert results to DataFrame
    df = pd.DataFrame(
        results,
        columns=[
            "VIN",
            "VehicleType",
            "Manufacturer",
            "Model",
            "Year",
            "FuelType",
            "Colors",
            "Horsepower",
            "SalePrice",
            "PurchasePrice",
            "PurchaseDate",
            "TotalPartsCost",
            "Description",
        ],
    )

    # Adjust columns based on role
    if role == "Public" or role == "Salesperson":
        return df[
            [
                "VIN",
                "VehicleType",
                "Manufacturer",
                "Model",
                "Year",
                "FuelType",
                "Colors",
                "Horsepower",
                "SalePrice",
            ]
        ]
    elif role == "Inventory clerk":
        return df[
            [
                "VIN",
                "VehicleType",
                "Manufacturer",
                "Model",
                "Year",
                "FuelType",
                "Colors",
                "Horsepower",
                "PurchasePrice",
                "TotalPartsCost",
            ]
        ]
    elif role in ["Manager", "Owner"]:
        return df

    return df


def count_cars_with_pending_parts() -> int:
    """
    Counts the total number of vehicles with parts pending (status != 'Installed') using raw SQL.

    Returns:
        int: Count of vehicles with parts pending.
    """
    query = """
        SELECT COUNT(DISTINCT v.vehicle_identification_number) AS pending_parts_count
        FROM Vehicle v
        INNER JOIN PartsOrder po ON v.vehicle_identification_number = po.vehicle_identification_number
        INNER JOIN Part p ON po.order_number = p.order_number
        WHERE p.status != 'Installed' -- Parts not yet installed
        AND v.vehicle_identification_number NOT IN (
            SELECT vehicle_identification_number 
            FROM SaleTransaction
        ) -- Exclude sold vehicles
    """

    with create_session() as session:
        result = session.execute(query).fetchone()

    pending_count = result["pending_parts_count"] if result else 0
    return pending_count


def count_available_cars() -> int:
    """
    Counts the total number of cars available for sale (without pending parts) using raw SQL.

    Returns:
        int: Count of vehicles available for sale.
    """
    query = """
        SELECT COUNT(DISTINCT v.vehicle_identification_number) AS available_for_sale
        FROM Vehicle v
        LEFT JOIN PartsOrder po ON v.vehicle_identification_number = po.vehicle_identification_number
        WHERE NOT EXISTS (
            SELECT 1 
            FROM Part p
            INNER JOIN PartsOrder po_sub ON p.order_number = po_sub.order_number
            WHERE po_sub.vehicle_identification_number = v.vehicle_identification_number
              AND p.status != 'Installed'
        ) -- Ensure no pending parts
        AND v.vehicle_identification_number NOT IN (
            SELECT vehicle_identification_number 
            FROM SaleTransaction
        ) -- Ensure vehicle is not sold
    """

    with create_session() as session:
        result = session.execute(query).fetchone()
        return result["available_for_sale"] if result else 0


def seller_history_report() -> pd.DataFrame:
    """
    Generates the Seller History Report, showing details for each seller,
    including total vehicles sold, average purchase price, average parts quantity,
    and average parts cost per vehicle, with highlighting criteria.

    Returns:
        pd.DataFrame: DataFrame containing the seller history report, with a flag for highlighting rows.
    """
    # SQL query to fetch seller history report data
    query = """
        SELECT 
            CASE 
                WHEN bc.business_name IS NOT NULL THEN bc.business_name
                ELSE CONCAT(ic.first_name, ' ', ic.last_name)
            END AS SellerName,
            
            COUNT(pt.vehicle_identification_number) AS TotalVehiclesSold,
            ROUND(AVG(pt.purchase_price), 2) AS AvgPurchasePrice,
            
            AVG(
                (SELECT COALESCE(SUM(p.quantity), 0) 
                 FROM Part p 
                 INNER JOIN PartsOrder po ON po.order_number = p.order_number 
                 WHERE po.vehicle_identification_number = pt.vehicle_identification_number)
            ) AS AvgPartsQuantityPerVehicle,
            
            AVG(
                (SELECT COALESCE(SUM(p.quantity * p.unit_price), 0) 
                 FROM Part p 
                 INNER JOIN PartsOrder po ON po.order_number = p.order_number 
                 WHERE po.vehicle_identification_number = pt.vehicle_identification_number)
            ) AS AvgPartsCostPerVehicle

        FROM PurchaseTransaction pt
        LEFT JOIN BusinessCustomer bc ON pt.customer_id = bc.customer_id
        LEFT JOIN IndividualCustomer ic ON pt.customer_id = ic.customer_id

        GROUP BY pt.customer_id
        ORDER BY 
            TotalVehiclesSold DESC, 
            AvgPurchasePrice ASC;
    """

    # Execute query and fetch data
    with create_session() as session:
        result = session.execute(query).fetchall()

    # Convert the result to a DataFrame
    columns = [
        "Seller Name",
        "Total Vehicles Sold",
        "Avg Purchase Price",
        "Avg Parts Quantity Per Vehicle",
        "Avg Parts Cost Per Vehicle",
    ]
    df = pd.DataFrame(result, columns=columns)

    return df


def average_inventory_time_report() -> pd.DataFrame:
    """
    Generates the Average Inventory Time (AVT) report based on vehicle type.

    Returns:
        pd.DataFrame: DataFrame containing the average inventory time for each vehicle type.
    """
    query = """
        SELECT 
            vt.vehicle_type AS VehicleType,
            CASE 
                WHEN COUNT(st.sold_on) = 0 THEN 'N/A' 
                ELSE ROUND(AVG(DATEDIFF(st.sold_on, pt.purchased_on) + 1), 2) 
            END AS AvgInventoryTime
        FROM Vehicle v
        JOIN VehicleType vt ON v.vehicle_type = vt.vehicle_type
        LEFT JOIN PurchaseTransaction pt ON v.vehicle_identification_number = pt.vehicle_identification_number
        LEFT JOIN SaleTransaction st ON v.vehicle_identification_number = st.vehicle_identification_number
        # WHERE st.sold_on >= pt.purchased_on  -- Ensure sold_on is after or on purchased_on
        GROUP BY vt.vehicle_type
        ORDER BY vt.vehicle_type ASC;
    """

    with create_session() as session:
        result = session.execute(query).fetchall()

    # Define column names based on query results
    columns = ["Vehicle Type", "Avg Inventory Time"]
    df = pd.DataFrame(result, columns=columns)

    return df


def price_per_condition_report():
    """
    Generates a Price per Condition (PPC) Report, displaying the average purchase price
    for each vehicle type and condition in a pivoted table format.

    Returns:
        pd.DataFrame: A DataFrame containing the average purchase price per condition
                      for each vehicle type. Entries with no purchase records show $0.
    """
    # SQL query to calculate average purchase price per vehicle type and condition
    query = """
        SELECT 
            v.vehicle_type AS VehicleType,
            COALESCE(AVG(CASE WHEN v.condition = 'Excellent' THEN pt.purchase_price END), 0) AS Excellent,
            COALESCE(AVG(CASE WHEN v.condition = 'Very Good' THEN pt.purchase_price END), 0) AS VeryGood,
            COALESCE(AVG(CASE WHEN v.condition = 'Good' THEN pt.purchase_price END), 0) AS Good,
            COALESCE(AVG(CASE WHEN v.condition = 'Fair' THEN pt.purchase_price END), 0) AS Fair
        FROM Vehicle v
        LEFT JOIN PurchaseTransaction pt ON v.vehicle_identification_number = pt.vehicle_identification_number
        GROUP BY v.vehicle_type
        ORDER BY v.vehicle_type ASC;
    """

    # Execute query and fetch results
    with create_session() as session:
        result = session.execute(text(query)).fetchall()

    # Convert results to DataFrame with specified columns
    columns = ["Vehicle Type", "Excellent", "Very Good", "Good", "Fair"]
    df = pd.DataFrame(result, columns=columns)

    return df


def parts_statistics_report() -> pd.DataFrame:
    """
    Generates the Parts Statistics Report to assist North Avenue Automotive in analyzing parts expenses by vendor.

    Returns:
        pd.DataFrame: A DataFrame containing vendor names, total parts quantity, and total dollar amount spent on parts,
                      sorted by total dollar amount spent in descending order.
    """
    query = """
        SELECT 
            v.name AS VendorName,
            SUM(p.quantity) AS TotalPartsQuantity,
            SUM(p.unit_price * p.quantity) AS TotalAmountSpent
        FROM Vendor v
        JOIN PartsOrder po ON v.name = po.name
        JOIN Part p ON po.order_number = p.order_number
        GROUP BY v.name
        ORDER BY TotalAmountSpent DESC
    """

    with create_session() as session:
        result = session.execute(query).fetchall()

    # Define column names based on the query output
    columns = ["Vendor Name", "Total Parts Quantity", "Total Amount Spent"]
    df = pd.DataFrame(result, columns=columns)

    return df


def monthly_sales_summary() -> pd.DataFrame:
    """
    Generates a monthly summary of sales transactions, showing total vehicles sold,
    gross sales income, and net income by year and month.

    Returns:
        pd.DataFrame: A DataFrame containing the monthly sales summary.
    """
    query = """
        SELECT 
            YEAR(st.sold_on) AS Year,
            MONTH(st.sold_on) AS Month,
            COUNT(st.vehicle_identification_number) AS VehiclesSold,
            SUM(st.sale_price) AS GrossSalesIncome,
            SUM(st.sale_price - pt.purchase_price - IFNULL(po.total_cost, 0)) AS NetIncome
        FROM SaleTransaction st
        JOIN PurchaseTransaction pt ON st.vehicle_identification_number = pt.vehicle_identification_number
        LEFT JOIN (
            SELECT 
                po.vehicle_identification_number, 
                SUM(po.total_cost) AS total_cost
            FROM PartsOrder po
            GROUP BY po.vehicle_identification_number
        ) po ON st.vehicle_identification_number = po.vehicle_identification_number
        GROUP BY Year, Month
        HAVING VehiclesSold > 0
        ORDER BY Year DESC, Month DESC;
    """

    with create_session() as session:
        result = session.execute(query).fetchall()

    columns = ["Year", "Month", "Vehicles Sold", "Gross Sales Income", "Net Income"]
    df = pd.DataFrame(result, columns=columns)

    return df


def monthly_sales_drilldown(year: str, month: str) -> pd.DataFrame:
    """
    Generates a drilldown report of top-performing salespeople for a specified month and year.

    Parameters:
        year (str): The year for which to retrieve the drilldown report.
        month (str): The month (in MM format) for which to retrieve the drilldown report.

    Returns:
        pd.DataFrame: A DataFrame containing the monthly sales drilldown by salesperson.
    """
    query = """
        SELECT 
            u.first_name AS SalespersonFirstName,
            u.last_name AS SalespersonLastName,
            COUNT(st.vehicle_identification_number) AS VehiclesSold,
            SUM(st.sale_price) AS TotalSales
        FROM SaleTransaction st
        JOIN User u ON st.username = u.username
        WHERE   YEAR(st.sold_on) = :year AND MONTH(st.sold_on) = :month
        GROUP BY u.username
        ORDER BY VehiclesSold DESC, TotalSales DESC;
    """

    params = {"year": year, "month": month}

    with create_session() as session:
        result = session.execute(query, params).fetchall()

    columns = ["First Name", "Last Name", "Vehicles Sold", "Total Sales"]
    df = pd.DataFrame(result, columns=columns)
    return df


def fetch_vendors():
    """
    Fetches vendor names from the database using raw SQL.

    Returns:
        list: A list of vendor names.
    """
    query = "SELECT name FROM Vendor"
    with create_session() as session:
        vendors = session.execute(query).fetchall()
    return [vendor[0] for vendor in vendors]


def add_parts_order(vin: str, vendor_name: str, parts: list) -> bool:
    """
    Adds a parts order for a specific vehicle, including multiple parts.

    Parameters:
        vin (str): Vehicle Identification Number.
        vendor_name (str): Name of the vendor.
        parts (list): List of dictionaries, each representing a part.

    Returns:
        bool: True if the order and parts were added successfully, False otherwise.
    """
    try:
        with create_session() as session:
            # Step 1: Generate a new `order_number` for the VIN
            query = "SELECT COUNT(*) FROM PartsOrder WHERE vehicle_identification_number = :vin"
            count = session.execute(query, {"vin": vin}).scalar()
            sequential_number = count + 1
            order_number = f"{vin}-{str(sequential_number).zfill(3)}"

            # Step 2: Calculate the total cost of all parts
            total_cost = round(
                sum(part["unit_price"] * part["quantity"] for part in parts), 2
            )

            # Step 3: Insert the order into `PartsOrder`
            parts_order_query = """
                INSERT INTO PartsOrder (vehicle_identification_number, name, order_number, total_cost)
                VALUES (:vin, :vendor_name, :order_number, :total_cost)
            """
            session.execute(
                parts_order_query,
                {
                    "vin": vin,
                    "vendor_name": vendor_name,
                    "order_number": order_number,
                    "total_cost": total_cost,
                },
            )

            # Step 4: Insert each part into the `Part` table
            for part in parts:
                part_query = """
                    INSERT INTO Part (order_number, vendor_parts_number, description, quantity, status, unit_price)
                    VALUES (:order_number, :vendor_part_number, :description, :quantity, :status, :unit_price)
                """
                session.execute(
                    part_query,
                    {
                        "order_number": order_number,
                        "vendor_part_number": part["vendor_part_number"],
                        "description": part["part_description"],
                        "quantity": part["quantity"],
                        "status": part["part_status"],
                        "unit_price": part["unit_price"],
                    },
                )

            # Commit the transaction
            session.commit()
            return True
    except Exception as e:
        print(f"Error adding parts order: {e}")
        return False


def add_vendor(
    name: str,
    phone_number: str,
    address_street: str,
    address_city: str,
    address_state: str,
    address_postal_code: str,
) -> bool:
    """
    Adds a new vendor to the database.

    Parameters:
        name (str): Name of the vendor.
        phone_number (str): Phone number of the vendor.
        address_street (str): Street address of the vendor.
        address_city (str): City of the vendor.
        address_state (str): State of the vendor.
        address_postal_code (str): Postal code of the vendor.

    Returns:
        bool: True if the vendor was added successfully, False otherwise.
    """
    # SQL query to insert a new vendor
    query = """
        INSERT INTO Vendor (name, phone_number, address_street, address_city, address_state, address_postal_code)
        VALUES (:name, :phone_number, :address_street, :address_city, :address_state, :address_postal_code)
    """

    try:
        with create_session() as session:
            session.execute(
                query,
                {
                    "name": name,
                    "phone_number": phone_number,
                    "address_street": address_street,
                    "address_city": address_city,
                    "address_state": address_state,
                    "address_postal_code": address_postal_code,
                },
            )
            session.commit()  # Commit the transaction
            return True
    except Exception as e:
        # Handle exceptions (you can log this error or print it)
        print(f"Error adding vendor: {e}")
        return False


def add_vehicle(
    customer_id,
    vin,
    vehicle_type,
    manufacturer,
    condition,
    model,
    year,
    fuel_type,
    horsepower,
    description="",
):
    """
    Adds a new vehicle and associated customer data to the database.

    Parameters:
        vin (str): Vehicle Identification Number.
        vehicle_type (str): Type of the vehicle.
        manufacturer (str): Vehicle manufacturer.
        model (str): Vehicle model.
        year (int): Manufacturing year.
        fuel_type (str): Type of fuel.
        horsepower (int): Vehicle horsepower.
        color (str): Vehicle color.
        customer_type (str): Type of customer ("Individual" or "Business").
        first_name (str, optional): First name of the individual customer.
        last_name (str, optional): Last name of the individual customer.
        social_security_number (str, optional): SSN of the individual customer.
        business_name (str, optional): Name of the business customer.
        tax_id_number (str, optional): Tax ID of the business customer.
        primary_contact_name (str, optional): Primary contact name for the business.
        primary_contact_title (str, optional): Title of the primary contact.
        email (str, optional): Customer email.
        phone (str, optional): Customer phone number.
        street (str, optional): Street address of the customer.
        city (str, optional): City of the customer.
        state (str, optional): State of the customer.
        postal_code (str, optional): Postal code of the customer.

    Returns:
        bool: True if the vehicle and customer were added successfully, False otherwise.
    """
    with create_session() as session:
        # Insert vehicle data
        try:
            session.execute(
                """
                INSERT INTO Vehicle (vehicle_identification_number, vehicle_type, manufacturer_name, `condition`, model_name, `year`, fuel_type, horsepower, description)
                VALUES (:vin, :vehicle_type, :manufacturer, :condition, :model, :year, :fuel_type, :horsepower, :description)
                """,
                {
                    "vin": vin,
                    "vehicle_type": vehicle_type,
                    "manufacturer": manufacturer,
                    "condition": condition,
                    "model": model,
                    "year": year,
                    "fuel_type": fuel_type,
                    "horsepower": horsepower,
                    "description": description,
                },
            )

            if customer_id is None:
                return False

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error occurred: {e}")
            return False


def lookup_customers():
    """
    Looks up customer names from the Customer table.

    Returns:
        List[str]: A list of customer names.
    """
    with create_session() as session:
        # SQL query to select customer names
        query = "SELECT social_security_number AS SSN FROM IndividualCustomer WHERE social_security_number IS NOT NULL"
        query += " UNION SELECT tax_identification_number AS TaxID FROM BusinessCustomer WHERE tax_identification_number IS NOT NULL"

        results = session.execute(query).fetchall()

    # Extracting full names into a list
    customer_names = [result[0] for result in results]

    return customer_names


def add_customer(
    customer_type,
    first_name,
    last_name,
    phone,
    street,
    city,
    state,
    postal_code,
    email=None,
    social_security_number=None,
    business_name=None,
    tax_id_number=None,
    primary_contact_name=None,
    primary_contact_title=None,
):
    """
    Adds a new customer to the database.

    Parameters:
        customer_type (str): Type of customer ("Individual" or "Business").
        first_name (str, optional): First name of the individual customer.
        last_name (str, optional): Last name of the individual customer.
        social_security_number (str, optional): SSN of the individual customer.
        business_name (str, optional): Name of the business customer.
        tax_id_number (str, optional): Tax ID of the business customer.
        primary_contact_name (str, optional): Primary contact name for the business.
        primary_contact_title (str, optional): Title of the primary contact.
        email (str, optional): Customer email.
        phone (str, optional): Customer phone number.
        street (str, optional): Street address of the customer.
        city (str, optional): City of the customer.
        state (str, optional): State of the customer.
        postal_code (str, optional): Postal code of the customer.

    Returns:
        int: The customer ID of the newly created customer.
    """
    with create_session() as session:
        try:
            # Insert customer data into the generic Customer table
            session.execute(
                """
                INSERT INTO Customer (email, phone_number, address_street, address_city, address_state, address_postal_code)
                VALUES (:email, :phone, :street, :city, :state, :postal_code)
                """,
                {
                    "email": email,
                    "phone": phone,
                    "street": street,
                    "city": city,
                    "state": state,
                    "postal_code": postal_code,
                },
            )

            # Fetch the customer ID of the newly inserted customer
            customer_id = session.execute("SELECT LAST_INSERT_ID()").scalar()

            # Insert into specific customer table based on customer type
            if customer_type == "Individual":
                session.execute(
                    """
                    INSERT INTO IndividualCustomer (customer_id, first_name, last_name, social_security_number)
                    VALUES (:customer_id, :first_name, :last_name, :ssn)
                    """,
                    {
                        "customer_id": customer_id,
                        "first_name": first_name,
                        "last_name": last_name,
                        "ssn": social_security_number,
                    },
                )
            elif customer_type == "Business":
                session.execute(
                    """
                    INSERT INTO BusinessCustomer (customer_id, business_name, tax_identification_number, primary_contact_first_name, primary_contact_last_name, primary_contact_title)
                    VALUES (:customer_id, :business_name, :tax_id, :primary_contact_first_name, :primary_contact_last_name, :primary_contact_title)
                    """,
                    {
                        "customer_id": customer_id,
                        "business_name": business_name,
                        "tax_id": tax_id_number,
                        "primary_contact_first_name": primary_contact_name,
                        "primary_contact_last_name": primary_contact_name,
                        "primary_contact_title": primary_contact_title,
                    },
                )
            session.commit()
            return customer_id  # Return the ID of the newly created customer
        except Exception as e:
            session.rollback()
            print(f"Error occurred while adding customer: {e}")
            return None  # Return None on failure


def fetch_customer_id(customer):
    """
    Looks up customer names from the Customer table.

    Returns:
        List[str]: A list of customer names.
    """
    with create_session() as session:
        # SQL query to select customer names
        query = "SELECT customer_id FROM IndividualCustomer WHERE social_security_number = :customer"
        query += " UNION SELECT customer_id FROM BusinessCustomer WHERE tax_identification_number = :customer"

        results = session.execute(query, {"customer": customer}).fetchall()

    # Extracting full names into a list
    customer_ids = [result[0] for result in results]

    return customer_ids


def add_purchase_transaction(vin, customer_id, username, purchase_price, purchase_date):
    """
    Inserts a new purchase transaction into the PurchaseTransaction table.

    Parameters:
        vin (str): Vehicle Identification Number.
        customer_id (int): ID of the customer making the purchase.
        username (str): Username of the user making the purchase.
        purchase_price (float): Price at which the vehicle was purchased.
        purchase_date (datetime): Date of purchase.

    Returns:
        bool: True if the transaction was added successfully, False otherwise.
    """
    with create_session() as session:
        try:
            session.execute(
                """
                INSERT INTO PurchaseTransaction (vehicle_identification_number, customer_id, username, purchase_price, purchased_on)
                VALUES (:vin, :customer_id, :username, :purchase_price, :purchase_date)
                """,
                {
                    "vin": vin,
                    "customer_id": customer_id,
                    "username": username,
                    "purchase_price": purchase_price,
                    "purchase_date": purchase_date,
                },
            )
            session.commit()
            return True  # Return True if the insertion is successful
        except Exception as e:
            session.rollback()
            print(f"Error occurred while adding purchase transaction: {e}")
            return False  # Return False if there was an error


def add_vehicle_colors(vin, colors):
    """
    Inserts the VIN and associated color(s) into the VehicleColor table.

    Parameters:
        vin (str): Vehicle Identification Number.
        colors (list): List of color names to associate with the vehicle.

    Returns:
        bool: True if the colors were added successfully, False otherwise.
    """
    with create_session() as session:
        try:
            for color in colors:
                session.execute(
                    """
                    INSERT INTO VehicleColor (vehicle_identification_number, color_name)
                    VALUES (:vin, :color)
                    """,
                    {"vin": vin, "color": color},
                )
            session.commit()
            return True  # Return True if the insertion is successful
        except Exception as e:
            session.rollback()
            print(f"Error occurred while adding vehicle colors: {e}")
            return False  # Return False if there was an error


def add_vehicle_and_related_data(
    vin,
    vehicle_type,
    manufacturer,
    condition,
    model,
    year,
    fuel_type,
    horsepower,
    color,
    customer_id,
    username,
    purchase_price,
    purchase_date,
    description="",
):
    """
    Adds a new vehicle, associated customer data, and colors to the database.

    Parameters:
        ... (same as in previous functions) ...

    Returns:
        bool: True if all operations were successful, False otherwise.
    """
    try:

        # Add the vehicle
        vehicle_success = add_vehicle(
            customer_id,
            vin,
            vehicle_type,
            manufacturer,
            condition,
            model,
            year,
            fuel_type,
            horsepower,
            description,
        )

        if vehicle_success:
            color_success = add_vehicle_colors(vin, color)
            purchase_success = add_purchase_transaction(
                vin, customer_id, username, purchase_price, purchase_date
            )

            # Check if both color and purchase transactions were successful
            if color_success and purchase_success:
                return True
            else:
                return False
        else:
            return False

    except Exception as e:
        print(f"Error occurred while adding vehicle and related data: {e}")
        return False


def fetch_distinct_values_from_table(table_name: str, column_name: str) -> List[str]:
    """
    Fetches distinct values from a given table and column using raw SQL.

    Parameters:
        table_name (str): The name of the table.
        column_name (str): The name of the column to fetch distinct values from.

    Returns:
        List[str]: A list of distinct values from the specified column.
    """
    query = f"SELECT DISTINCT {column_name} FROM {table_name}"

    with create_session() as session:
        results = session.execute(query).fetchall()

    return [result[0] for result in results]


def get_vehicle_counts() -> tuple:
    """
    Retrieves the total number of vehicles available for sale and those with pending parts.

    Parameters:
        None

    Returns:
        tuple: A tuple containing the count of vehicles available for sale and those with pending parts.
    """
    return count_available_cars(), count_cars_with_pending_parts()


def get_vehicle_details_for_public(
    vin: str = None, role: str = "Public"
) -> pd.DataFrame:
    """
    Searches vehicles based on the provided criteria using raw SQL.

    Parameters:
        vehicle_type (str, optional): The type of vehicle (e.g., Sedan, SUV).
        manufacturer (str, optional): The vehicle manufacturer.
        year (int, optional): The manufacturing year.
        fuel_type (str, optional): The type of fuel used by the vehicle.
        color (str, optional): The color of the vehicle.
        keyword (str, optional): A keyword to search within the manufacturer, model, year, and description fields.
        vin (str, optional): Specific vehicle identification number to search for.
        vehicle_status (str, optional): Filter by vehicle status ("Sold", "Unsold").
        role (str): User role performing the search (e.g., Public, Salesperson, Manager, etc.).

    Returns:
        pd.DataFrame: DataFrame containing matching vehicle details, sorted by vehicle_identification_number.
    """
    query = """
        SELECT 
            v.vehicle_identification_number AS VIN,
            v.vehicle_type AS VehicleType,
            v.manufacturer_name AS Manufacturer,
            v.model_name AS Model,
            v.year AS Year,
            v.fuel_type AS FuelType,
            GROUP_CONCAT(DISTINCT vc.color_name SEPARATOR ', ') AS Colors,
            v.horsepower AS Horsepower,
            -- Calculate SalePrice dynamically using aggregated parts cost
            CASE
                WHEN st.sale_price IS NOT NULL THEN st.sale_price
                ELSE ROUND((1.25 * pt.purchase_price) + (1.1 * IFNULL(po_aggregated.TotalPartsCost, 0)), 2)
            END AS SalePrice,
            st.sold_on AS SaleDate,
            pt.purchase_price AS PurchasePrice,
            pt.purchased_on AS PurchaseDate,
            ROUND(COALESCE(po_aggregated.TotalPartsCost, 0), 2) AS TotalPartsCost,
            v.description AS Description
        FROM Vehicle v
        LEFT JOIN VehicleColor vc ON v.vehicle_identification_number = vc.vehicle_identification_number
        LEFT JOIN SaleTransaction st ON v.vehicle_identification_number = st.vehicle_identification_number
        LEFT JOIN PurchaseTransaction pt ON v.vehicle_identification_number = pt.vehicle_identification_number
        -- Pre-aggregate PartsOrder costs by vehicle
        LEFT JOIN (
            SELECT 
                vehicle_identification_number, 
                SUM(total_cost) AS TotalPartsCost
            FROM PartsOrder
            GROUP BY vehicle_identification_number
        ) po_aggregated ON v.vehicle_identification_number = po_aggregated.vehicle_identification_number
    """

    # Role-Based Filtering
    if role in ["Public", "Salesperson"]:
        query += """
            WHERE st.sale_price IS NULL -- Unsold vehicles only
            AND NOT EXISTS (
                SELECT 1 FROM Part p
                INNER JOIN PartsOrder po_sub ON p.order_number = po_sub.order_number
                WHERE po_sub.vehicle_identification_number = v.vehicle_identification_number
                  AND p.status != 'Installed'
            ) -- No pending parts
        """
    elif role in ["Manager", "Owner"]:
        query += "WHERE 1=1"  # Show details for sold vehicles as well for manager and owner. Improve this condition if possible.
    else:
        query += "WHERE st.sale_price IS NULL"  # Show all unsold vehicles, with or without pending parts

    if vin:
        query += " AND v.vehicle_identification_number = :vin"

    query += """
    GROUP BY 
        v.vehicle_identification_number, 
        v.vehicle_type, 
        v.manufacturer_name, 
        v.model_name, 
        v.year, 
        v.fuel_type, 
        v.horsepower, 
        st.sale_price,
        st.sold_on,
        pt.purchased_on, 
        pt.purchase_price,
        v.description
    ORDER BY v.vehicle_identification_number ASC
    """

    # Execute query and fetch results
    with create_session() as session:
        # Execute the query with the provided VIN
        result = session.execute(query, {"vin": vin}).fetchall()

    # Convert results to DataFrame
    df = pd.DataFrame(
        result,
        columns=[
            "VIN",
            "VehicleType",
            "Manufacturer",
            "Model",
            "Year",
            "FuelType",
            "Colors",
            "Horsepower",
            "SalePrice",
            "SaleDate",
            "PurchasePrice",
            "PurchaseDate",
            "TotalPartsCost",
            "Description",
        ],
    )

    # Adjust columns based on role
    if role == "Public" or role == "Salesperson":
        return pd.melt(
            df[
                [
                    "VIN",
                    "VehicleType",
                    "Manufacturer",
                    "Model",
                    "Year",
                    "FuelType",
                    "Colors",
                    "Horsepower",
                    "Description",
                    "SalePrice",
                ]
            ],
            var_name="Attribute",
            value_name="Value",
        )
    else:
        return pd.melt(
            df[
                [
                    "VIN",
                    "VehicleType",
                    "Manufacturer",
                    "Model",
                    "Year",
                    "FuelType",
                    "Colors",
                    "Horsepower",
                    "Description",
                    "TotalPartsCost",
                    "PurchasePrice",
                    "PurchaseDate",
                    "SalePrice",
                    "SaleDate",
                ]
            ],
            var_name="Attribute",
            value_name="Value",
        )


def get_vehicle_details_for_sale(vin: str) -> Optional[Dict[str, str]]:
    """
    Fetches vehicle details for a vehicle that is eligible for sale based on the provided VIN.
    The details include vehicle type, manufacturer, model, year, fuel type, horsepower, colors,
    condition, description, purchase price, purchase date, and calculated sale price.

    Parameters:
        vin (str): The VIN of the vehicle to fetch details for.

    Returns:
        Optional[Dict[str, str]]: A dictionary containing the vehicle's details if found and eligible for sale,
                                  None otherwise.
    """
    with create_session() as session:
        # SQL query to fetch vehicle details for sale
        query = """
            SELECT 
                v.vehicle_identification_number AS VIN,
                v.vehicle_type AS VehicleType,
                v.manufacturer_name AS Manufacturer,
                v.model_name AS Model,
                v.year AS Year,
                v.fuel_type AS FuelType,
                GROUP_CONCAT(DISTINCT vc.color_name SEPARATOR ', ') AS Colors,
                v.horsepower AS Horsepower,
                -- Calculate SalePrice dynamically using aggregated parts cost
                CASE
                    WHEN st.sale_price IS NOT NULL THEN st.sale_price
                    ELSE ROUND((1.25 * pt.purchase_price) + (1.1 * IFNULL(po_aggregated.TotalPartsCost, 0)), 2)
                END AS SalePrice,
                st.sold_on,
                pt.purchase_price AS PurchasePrice,
                pt.purchased_on AS PurchaseDate,
                ROUND(COALESCE(po_aggregated.TotalPartsCost, 0), 2) AS TotalPartsCost,
                v.description AS Description,
                v.condition as VehicleCondition
            FROM Vehicle v
            LEFT JOIN VehicleColor vc ON v.vehicle_identification_number = vc.vehicle_identification_number
            LEFT JOIN SaleTransaction st ON v.vehicle_identification_number = st.vehicle_identification_number
            LEFT JOIN PurchaseTransaction pt ON v.vehicle_identification_number = pt.vehicle_identification_number
            -- Pre-aggregate PartsOrder costs by vehicle
            LEFT JOIN (
                SELECT 
                    vehicle_identification_number, 
                    SUM(total_cost) AS TotalPartsCost
                FROM PartsOrder
                GROUP BY vehicle_identification_number
            ) po_aggregated ON v.vehicle_identification_number = po_aggregated.vehicle_identification_number
            WHERE v.vehicle_identification_number = :vin
            AND v.vehicle_identification_number NOT IN (
                SELECT vehicle_identification_number 
                FROM SaleTransaction
            )  -- Ensure vehicle is not sold
            GROUP BY 
                v.vehicle_identification_number, 
                v.vehicle_type, 
                v.manufacturer_name, 
                v.model_name, 
                v.year, 
                v.fuel_type, 
                v.horsepower, 
                st.sale_price,
                st.sold_on,
                pt.purchased_on, 
                pt.purchase_price,
                v.description,
                v.condition
        """

        # Execute the query with the provided VIN
        result = session.execute(query, {"vin": vin}).fetchone()

        # If the vehicle is found, return the details as a dictionary
        if result:
            vehicle_details = {
                "VIN": result["VIN"],
                "VehicleType": result["VehicleType"],
                "Manufacturer": result["Manufacturer"],
                "Model": result["Model"],
                "Year": result["Year"],
                "FuelType": result["FuelType"],
                "Horsepower": result["Horsepower"],
                "Colors": result["Colors"],
                "Condition": result["VehicleCondition"],
                "Description": result["Description"],
                "PurchasePrice": result["PurchasePrice"],
                "PurchaseDate": result["PurchaseDate"],
                "SalePrice": result["SalePrice"],
            }
            return vehicle_details
        else:
            # Return None if the vehicle is not found or is not eligible for sale
            return None


def get_vehicle_details(vin: str = None, role: str = "Public") -> pd.DataFrame:
    """
    Searches vehicles based on the provided criteria using raw SQL.

    Parameters:
        vehicle_type (str, optional): The type of vehicle (e.g., Sedan, SUV).
        manufacturer (str, optional): The vehicle manufacturer.
        year (int, optional): The manufacturing year.
        fuel_type (str, optional): The type of fuel used by the vehicle.
        color (str, optional): The color of the vehicle.
        keyword (str, optional): A keyword to search within the manufacturer, model, year, and description fields.
        vin (str, optional): Specific vehicle identification number to search for.
        vehicle_status (str, optional): Filter by vehicle status ("Sold", "Unsold").
        role (str): User role performing the search (e.g., Public, Salesperson, Manager, etc.).

    Returns:
        pd.DataFrame: DataFrame containing matching vehicle details, sorted by vehicle_identification_number.
    """
    query = """
        SELECT 
            v.vehicle_identification_number AS VIN,
            v.vehicle_type AS VehicleType,
            v.manufacturer_name AS Manufacturer,
            v.model_name AS Model,
            v.year AS Year,
            v.fuel_type AS FuelType,
            GROUP_CONCAT(DISTINCT vc.color_name SEPARATOR ', ') AS Colors,
            v.horsepower AS Horsepower,
            -- Calculate SalePrice dynamically using aggregated parts cost
            CASE
                WHEN st.sale_price IS NOT NULL THEN st.sale_price
                ELSE ROUND((1.25 * pt.purchase_price) + (1.1 * IFNULL(po_aggregated.TotalPartsCost, 0)), 2)
            END AS SalePrice,
            st.sold_on AS SaleDate,
            pt.purchase_price AS PurchasePrice,
            pt.purchased_on AS PurchaseDate,
            ROUND(COALESCE(po_aggregated.TotalPartsCost, 0), 2) AS TotalPartsCost,
            v.description AS Description
        FROM Vehicle v
        LEFT JOIN VehicleColor vc ON v.vehicle_identification_number = vc.vehicle_identification_number
        LEFT JOIN SaleTransaction st ON v.vehicle_identification_number = st.vehicle_identification_number
        LEFT JOIN PurchaseTransaction pt ON v.vehicle_identification_number = pt.vehicle_identification_number
        -- Pre-aggregate PartsOrder costs by vehicle
        LEFT JOIN (
            SELECT 
                vehicle_identification_number, 
                SUM(total_cost) AS TotalPartsCost
            FROM PartsOrder
            GROUP BY vehicle_identification_number
        ) po_aggregated ON v.vehicle_identification_number = po_aggregated.vehicle_identification_number
    """

    # Role-Based Filtering
    if role in ["Public", "Salesperson"]:
        query += """
            WHERE st.sale_price IS NULL -- Unsold vehicles only
            AND NOT EXISTS (
                SELECT 1 FROM Part p
                INNER JOIN PartsOrder po_sub ON p.order_number = po_sub.order_number
                WHERE po_sub.vehicle_identification_number = v.vehicle_identification_number
                  AND p.status != 'Installed'
            ) -- No pending parts
        """
    else:
        query += "WHERE st.sale_price IS NULL"  # Show all unsold vehicles, with or without pending parts

    if vin:
        query += " AND v.vehicle_identification_number = :vin"

    query += """
    GROUP BY 
        v.vehicle_identification_number, 
        v.vehicle_type, 
        v.manufacturer_name, 
        v.model_name, 
        v.year, 
        v.fuel_type, 
        v.horsepower, 
        st.sale_price,
        st.sold_on,
        pt.purchased_on, 
        pt.purchase_price,
        v.description
    ORDER BY v.vehicle_identification_number ASC
    """

    # Execute query and fetch results
    with create_session() as session:
        # Execute the query with the provided VIN
        result = session.execute(query, {"vin": vin}).fetchall()

    # Convert results to DataFrame
    df = pd.DataFrame(
        result,
        columns=[
            "VIN",
            "VehicleType",
            "Manufacturer",
            "Model",
            "Year",
            "FuelType",
            "Colors",
            "Horsepower",
            "SalePrice",
            "SaleDate",
            "PurchasePrice",
            "PurchaseDate",
            "TotalPartsCost",
            "Description",
        ],
    )

    # Adjust columns based on role
    if role == "Public" or role == "Salesperson":
        return pd.melt(
            df[
                [
                    "VIN",
                    "VehicleType",
                    "Manufacturer",
                    "Model",
                    "Year",
                    "FuelType",
                    "Colors",
                    "Horsepower",
                    "Description",
                    "SalePrice",
                ]
            ],
            var_name="Attribute",
            value_name="Value",
        )
    else:
        return pd.melt(
            df[
                [
                    "VIN",
                    "VehicleType",
                    "Manufacturer",
                    "Model",
                    "Year",
                    "FuelType",
                    "Colors",
                    "Horsepower",
                    "Description",
                    "TotalPartsCost",
                    "PurchasePrice",
                    "PurchaseDate",
                    "SalePrice",
                    "SaleDate",
                ]
            ],
            var_name="Attribute",
            value_name="Value",
        )


def get_vehicle_parts(vin: str):
    """
    Fetches the vehicle details and associated parts order information for a specific vehicle.

    Parameters:
        vin (str): The Vehicle Identification Number (VIN) of the vehicle.

    Returns:
        tuple: A tuple containing two elements:
            - vehicle_details (dict): A dictionary containing the vehicle details.
            - parts_orders (list): A list of dictionaries containing parts order details.
    """

    # Query for parts order details
    parts_query = """
    SELECT 
        po.order_number AS OrderNumber,
        p.vendor_parts_number AS VendorPartNumber,
        p.description AS PartDescription,
        p.quantity AS Quantity,
        p.status AS PartStatus,
        p.unit_price AS UnitPrice,
        v.name AS VendorName
    FROM 
        PartsOrder po
    JOIN Part p ON po.order_number = p.order_number
    JOIN Vendor v ON po.name = v.name
    WHERE po.vehicle_identification_number = :vin;
    """

    # Initialize results variables
    parts_orders = []

    with create_session() as session:
        # Execute parts orders query
        parts_result = session.execute(parts_query, {"vin": vin}).fetchall()
        for part in parts_result:
            parts_orders.append(dict(part))

    return parts_orders


def update_part_status(
    order_number: str, vendor_part_number: str, new_status: str
) -> bool:
    """
    Updates the status of a part based on the provided order number and vendor part number.

    Parameters:
        order_number (str): The order number associated with the part.
        vendor_part_number (str): The vendor part number.
        new_status (str): The new status to set (Ordered, Received, or Installed).

    Returns:
        bool: True if the status update is successful, False otherwise.
    """
    # Define valid status transitions
    valid_status_transitions = {
        "Ordered": ["Received", "Installed"],
        "Received": ["Installed"],
        "Installed": [],
    }

    with create_session() as session:
        current_status = session.execute(
            """
            SELECT status
            FROM Part
            WHERE order_number = :order_number AND vendor_parts_number = :vendor_part_number
            """,
            {"order_number": order_number, "vendor_part_number": vendor_part_number},
        ).fetchone()

        if not current_status:
            return False

        current_status = current_status[0]

        # Check if the new status is a valid transition
        if new_status in valid_status_transitions.get(current_status, []):
            # Update the part status
            session.execute(
                """
                UPDATE Part
                SET status = :new_status
                WHERE order_number = :order_number AND vendor_parts_number = :vendor_part_number
                """,
                {
                    "new_status": new_status,
                    "order_number": order_number,
                    "vendor_part_number": vendor_part_number,
                },
            )
            session.commit()
            return True

        return False


def record_sale(
    vin: str, customer_identifier: str, username: str, sale_date: str, sale_price: float
) -> str:
    """
    Records a sale in the SalesTransaction table.

    Parameters:
        vin (str): Vehicle Identification Number.
        customer_identifier (str): SSN or Tax ID of the customer.
        username (str): Username of the salesperson.
        sale_date (str): Date of the sale in YYYY-MM-DD format.
        sale_price (float): Sale price of the vehicle.

    Returns:
        str: Success or error message indicating the result of the operation.
    """
    with create_session() as session:

        # Insert the sale transaction
        sale_query = """
            INSERT INTO SaleTransaction (
                vehicle_identification_number,
                customer_id,
                username,
                sold_on,
                sale_price
            )
            VALUES (
                :vin,
                :customer_id,
                :username,
                :sale_date,
                :sale_price
            )
        """

        try:
            session.execute(
                sale_query,
                {
                    "vin": vin,
                    "customer_id": customer_identifier,
                    "username": username,
                    "sale_date": sale_date,
                    "sale_price": sale_price,
                },
            )
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False


def get_purchase_details(vin: str) -> Optional[Dict[str, str]]:
    """
    Fetches customer contact details and inventory clerk's information for a purchased vehicle.

    Parameters:
        vin (str): The VIN of the vehicle to fetch purchase details for.

    Returns:
        Optional[Dict[str, str]]: A dictionary containing seller's contact details and inventory clerk's information,
                                  or None if the vehicle has not been purchased.
    """
    with create_session() as session:
        # Step 1: Check if the VIN exists in the PurchaseTransaction table and fetch customer_id and username
        purchase_query = """
            SELECT 
                pt.customer_id AS CustomerID,
                pt.username AS ClerkUsername
            FROM PurchaseTransaction pt
            WHERE pt.vehicle_identification_number = :vin
        """
        purchase_result = session.execute(purchase_query, {"vin": vin}).fetchone()

        if not purchase_result:
            # Return None if the vehicle is not in PurchaseTransaction
            return None

        # Extract customer_id and username
        customer_id = purchase_result["CustomerID"]
        clerk_username = purchase_result["ClerkUsername"]

        # Step 2: Fetch customer contact details
        customer_query = """
            SELECT 
                email AS CustomerEmail,
                phone_number AS CustomerPhone,
                CONCAT(address_street, ', ', address_city, ', ', address_state, ' ', address_postal_code) AS FullAddress
            FROM Customer
            WHERE id = :customer_id
        """
        customer_result = session.execute(
            customer_query, {"customer_id": customer_id}
        ).fetchone()

        # Step 3: Fetch inventory clerk details from the User table
        clerk_query = """
            SELECT 
                first_name AS ClerkFirstName,
                last_name AS ClerkLastName,
                username AS ClerkUserName
            FROM User
            WHERE username = :username
        """
        clerk_result = session.execute(
            clerk_query, {"username": clerk_username}
        ).fetchone()

        # Combine results into a single dictionary
        if customer_result and clerk_result:
            return {
                "External Seller Email": customer_result["CustomerEmail"],
                "External Seller Phone": customer_result["CustomerPhone"],
                "External Seller Address": customer_result["FullAddress"],
                "Inventory Clerk First Name": clerk_result["ClerkFirstName"],
                "Inventory Clerk Last Name": clerk_result["ClerkLastName"],
                "Inventory Clerk Username": clerk_result["ClerkUserName"],
            }

        # Handle incomplete data gracefully
        return None


def get_sale_details(vin: str) -> Optional[Dict[str, str]]:
    """
    Fetches customer contact details and salesperson's information for a sold vehicle.

    Parameters:
        vin (str): The VIN of the vehicle to fetch sold details for.

    Returns:
        Optional[Dict[str, str]]: A dictionary containing buyer's contact details and inventory clerk's information,
                                  or None if the vehicle has not been purchased.
    """
    with create_session() as session:
        # Step 1: Check if the VIN exists in the PurchaseTransaction table and fetch customer_id and username
        purchase_query = """
            SELECT 
                customer_id AS CustomerID,
                username AS SaleUsername
            FROM SaleTransaction
            WHERE vehicle_identification_number = :vin
        """
        sale_result = session.execute(purchase_query, {"vin": vin}).fetchone()

        if not sale_result:
            # Return None if the vehicle is not in PurchaseTransaction
            return None

        # Extract customer_id and username
        customer_id = sale_result["CustomerID"]
        sale_username = sale_result["SaleUsername"]

        # Step 2: Fetch customer contact details
        customer_query = """
            SELECT 
                email AS CustomerEmail,
                phone_number AS CustomerPhone,
                CONCAT(address_street, ', ', address_city, ', ', address_state, ' ', address_postal_code) AS FullAddress
            FROM Customer
            WHERE id = :customer_id
        """
        customer_result = session.execute(
            customer_query, {"customer_id": customer_id}
        ).fetchone()

        # Step 3: Fetch inventory clerk details from the User table
        sale_query = """
            SELECT 
                first_name AS FirstName,
                last_name AS LastName,
                username AS UserName
            FROM User
            WHERE username = :username
        """
        person_result = session.execute(
            sale_query, {"username": sale_username}
        ).fetchone()

        # Combine results into a single dictionary
        if customer_result and person_result:
            return {
                "Customer Email": customer_result["CustomerEmail"],
                "Customer Phone": customer_result["CustomerPhone"],
                "Customer Address": customer_result["FullAddress"],
                "Seller First Name": person_result["FirstName"],
                "Seller Last Name": person_result["LastName"],
                "Seller Username": person_result["UserName"],
            }

        # Handle incomplete data gracefully
        return None


def update_status(new_status: str, vendor_part_number: str, order_number: str) -> bool:
    """
    Updates the status of a part in the Part table.

    Parameters:
        new_status (str): The new status to set (e.g., "Received", "Installed").
        vendor_part_number (str): The vendor part number of the part to update.
        order_number (str): The order number associated with the part.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    query = """
        UPDATE Part
        SET status = :new_status
        WHERE vendor_parts_number = :vendor_part_number
          AND order_number = :order_number
    """
    try:
        with create_session() as session:
            result = session.execute(
                text(query),
                {
                    "new_status": new_status,
                    "vendor_part_number": vendor_part_number,
                    "order_number": order_number,
                },
            )
            session.commit()
            return result.rowcount > 0  # Check if any rows were updated
    except Exception as e:
        print(f"Error updating part status: {e}")
        return False
