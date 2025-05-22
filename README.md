# Magento-Eglem Integration Script

This Python project is designed to integrate data between Magento and Eglem, updating product data as needed and recording the operations in a border database.

## Features

1. **Fetch Magento Products Data**  
   Retrieve product information from a Magento store.

2. **Get Updated Product Fields from Eglem**  
   Connect to the Eglem platform and fetch updated fields for products.

3. **Update Fields in Magento**  
   Push the updated product data from Eglem back into Magento.

4. **Record Operations in Border Database**  
   Log the details of executed updates into a separate border database for tracking and reporting purposes.

---

# Requirements

For MacOs:
    brew install mysql pkg-config
    pip install mysqlclient

# Activate virtual environment

python -m venv eglem-env

unix: source eglem-env/bin/activate
windows: .eglem-env/Scripts/Activate.ps1 (from PowerShell with administrator privilegies)
Set-ExecutionPolicy unrestricted
Get-ExecutionPolicy

# Install requirements

pip install -r requirements.txt

# Configuration

Use the enviroment variables inside .env

# Run application

python UpdateStockAndPrice.py  (it is used for updating the price and stock of the products)
