import pandas as pd
import csv
import datetime
import os
import glob

# Datestamp for the file name (compact format without separators)
file_datestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

# Datestamp for Magento fields (standard Magento format)
magento_datestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Output directory path
dir_path_output = "output"
outputDir = dir_path_output

# Create the output directory if it doesn't exist
if not os.path.isdir(outputDir):
    os.makedirs(outputDir)

def process_all_csv_files():
    # Get all CSV files in the current directory
    csv_files = glob.glob("*.csv")
    
    if not csv_files:
        print("No CSV files found in the current directory.")
        return
    
    for csv_file in csv_files:
        output_file = os.path.join(outputDir, f"import-customer-{file_datestamp}.csv")
        populateCustomersCSV(csv_file, output_file)

# Function to safely get the value of a column
def get_value(df, customer, column_name):
    if column_name in df.columns and pd.notna(customer.get(column_name)):
        return customer[column_name]
    return ''

def populateCustomersCSV(inputCSV, outputCSV):
    try:
        # Read data from the input CSV file
        df = pd.read_csv(inputCSV, 
                        sep=';', 
                        usecols=['id', 'id_ordine_esterno', 'data_ordine', 'email', 'ragione_sociale_spe', 
                                'indirizzo_spe', 'comune_spe', 'cap_spe', 'provincia_spe', 'cellulare_spe', 
                                'ragione_sociale', 'indirizzo', 'comune', 'cap', 'provincia'],
                        dtype={'cellulare_spe': str})
        
        # Header for the output file 
        header = ['email', '_website', '_store', 'confirmation', 'created_at', 'created_in', 'dob', 'firstname', 
                'gender', 'group_id', 'lastname', 'middlename', 'password_hash', 'prefix', 'rp_token', 
                'rp_token_created_at', 'store_id', 'suffix', 'taxvat', 'website_id', 'password', '_address_city', 
                '_address_company', '_address_country_id', '_address_fax', '_address_firstname', '_address_lastname', 
                '_address_middlename', '_address_postcode', '_address_prefix', '_address_region', '_address_street', 
                '_address_suffix', '_address_telephone', '_address_vat_id']
        
        # fields that we might need to add in the future: '_address_default_billing', '_address_default_shipping'
            
        with open(outputCSV, 'w', newline='', encoding='utf-8') as csvfile:
            csvWriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csvWriter.writerow(header)

            # Write a row for each customer
            for index, customer in df.iterrows():
                # Verify that the column exists and is not null
                ragione_sociale_spe = customer.get('ragione_sociale_spe', '') if 'ragione_sociale_spe' in df.columns else ''
                
                full_name = ragione_sociale_spe.split(' ', 1) if pd.notna(ragione_sociale_spe) else ['', '']
                firstname = full_name[0] if len(full_name) > 0 else ''
                lastname = full_name[1] if len(full_name) > 1 else ''
                email_lastname = full_name[1].replace(" ", ".")
                
                # Verify that the email column exists
                email_val = customer.get('email', '') if 'email' in df.columns else ''
                email = firstname + '.' + email_lastname + '@test.it' if firstname and lastname and email_lastname else (email_val if pd.notna(email_val) else '')
                
                cellulare= get_value(df, customer, 'cellulare_spe'.replace(".", "")) or '1'


                row = [
                    email,                                        # email
                    'bricozone',                                  # _website
                    'bz_it',                                      # _store
                    '',                                           # confirmation
                    magento_datestamp,                            # created_at
                    'Bricozone Italia',                           # created_in
                    '',                                           # dob
                    firstname,                                    # firstname
                    '',                                           # gender
                    '1',                                          # group_id
                    lastname,                                     # lastname
                    '',                                           # middlename
                    '',                                           # password_hash
                    '',                                           # prefix
                    '',                                           # rp_token
                    '',                                           # rp_token_created_at
                    '1',                                          # store_id
                    '',                                           # suffix
                    '',                                           # taxvat
                    '1',                                          # website_id
                    '',                                           # password
                    get_value(df, customer, 'comune_spe'),        # _address_city
                    ragione_sociale_spe,                          # _address_company
                    'IT',                                         # _address_country_id
                    '',                                           # _address_fax
                    firstname,                                    # _address_firstname
                    lastname,                                     # _address_lastname
                    '',                                           # _address_middlename
                    get_value(df, customer, 'cap_spe'),           # _address_postcode
                    '',                                           # _address_prefix
                    get_value(df, customer, 'provincia_spe'),     # _address_region
                    get_value(df, customer, 'indirizzo_spe'),     # _address_street
                    '',                                           # _address_suffix
                    cellulare,                                    # _address_telephone
                    ''                                            # _address_vat_id
                    # '1',                                        # _address_default_billing
                    # '1'                                         # _address_default_shipping
                ]
                csvWriter.writerow(row)
                
    except Exception as e:
        print(f"Error while processing the CSV file {inputCSV}: {e}")
        print(f"Check that the file exists and contains all the necessary columns.")
        print(f"Error details: Type: {type(e).__name__}, Message: {str(e)}")
       

process_all_csv_files()