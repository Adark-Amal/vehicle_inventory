### North Avenue Automotive

The North Avenue Automobile platform is designed to manage the inventory of vehicles, handle customer information, parts orders, and sales transactions. This web application allows various user roles (such as Inventory Clerks, Salespeople, Managers, and Owners) to perform different actions, including adding new vehicles, managing parts orders, searching for vehicles, adding and managing customers, and completing vehicle sales transactions.

The application provides a user-friendly interface built with Streamlit and stores data in a relational database (MySQL) via raw SQL queries.

---
### Features

* Vehicle Management
  * Add, view, and update vehicles in the inventory.
  * View and manage the status of vehicles (e.g., pending parts).
  * Search for vehicles based on multiple filters (e.g., vehicle type, manufacturer, color, etc.).

* Parts Order Management
  * Add parts orders, including vendor details, part description, quantity, price, and status.

* Customer Management
  * Add and manage customers, both individual and business customers.
  * Add customer details such as contact information, address, and social security or tax identification number.

* Sales Management
  * Process sales transactions, including assigning sales prices based on original purchase prices and parts costs.
  * Record the sale date and customer information.
  * Track vehicles that have been sold or are pending parts installation.

* Reporting
  * Generate reports such as Seller History Report, Average Inventory Time (AVT), Parts Statistics Report, and Monthly Sales Report.

---

### User Roles and Permissions
1. Public
   * Can search for vehicles and view available vehicles for sale.

2. Inventory Clerk
   * Can add new vehicles, manage parts orders, and update vehicle statuses (e.g., vehicles with pending parts).
   * Can view and update the status of parts.

3. Salesperson
   * Can add new customers (individual and business), and complete sales transactions by linking customers to vehicles.
   * Can view vehicles available for sale.

4. Manager
   * Has full access to all vehicle management and sales features.
   * Can access reports such as Monthly Sales Report, Seller History Report, etc.

5. Owner
   * Has all the permissions of a Manager, including access to all parts, vehicles, and transactions, and the ability to view and edit customer details.

---

### Setup

Prerequisites

* Python 3.7+
* MySQL database (or compatible SQL database)
* Streamlit for the front end
* SQLAlchemy for database queries
* Pandas for data manipulation

### Installation
1. Clone the repository:
    ```bash
    git clone https://github.gatech.edu/cs6400-2024-03-fall/cs6400-2024-03-Team098.git
    ```
2. Create a virtual environment
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3. Install required dependencies using `pip`
    ```bash
    pip install -r requirements.txt
    ```
4. Set up your MySQL database. You will need to create a MySQL database with the tables as described in the project structure. To setup database install MySQL and MySQL workbench on your computer and use the data import feature on workbench to load files from the `dumps` folder. Tables include;<br>

    * Vehicle
    * Customer
    * PartsOrder
    * SaleTransaction
    * Vendor
    * etc.
  
5. Create a `.env` file for storing environment variables such as the database connection string.
    ```env
    # Database configuration
    DB_USER=<username>
    DB_PASSWORD=<password>
    DB_HOST=localhost
    DB_PORT=3306
    DB_NAME=north_avenue

    # Secret key for session management
    SECRET_KEY=<generate secret key>  

    # Environment setting
    ENV=development
    ```

---

### How to Run the App
1. Start the Streamlit app by running the following command in your terminal
    ```bash
    streamlit run app.py
    ```
2. The application will open in your browser, and you can start interacting with the system by logging in as a user with the appropriate role. 
3. Images of features of the app can be found in the `images` directory


### Directory Structure
```bash
/project-root
│
├── app.py                    # Main Streamlit app
├── config.py                 # Loads database configurations
├── controllers/              # Contains logic for CRUD operations
├── db/                       # Database connection and session management
├── pages/                    # Pages for various features (e.g., add vehicle, search, sales)
├── utils/                    # Utility functions like authentication, constants, etc.
├── dumps/                    # Contains sql files for creating database and loading data
├── images/                   # Contains images of app features
├── requirements.txt          # List of dependencies
└── .env                      # Environment variables (e.g., database URL)
```

### License
This project is licensed under the MIT License.
