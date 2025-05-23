#!/usr/bin/env python3
"""
CategoryImporter.py
Import categories into Magento from Zangoo database
Fully parameterized for multiple stores
"""

import logging
from lib.helper.CategoryHelper import CategoryHelper
from lib.helper.CatalogImporterConfigHelper import config

logging.basicConfig(
    filename=config('LOGGING_FILE', default='category_import.log'),
    level=config('LOGGING_LEVEL', default='INFO'),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_stores_configuration():
    """
    Gets stores configuration from environment variables
    
    Returns:
        list: List of store configurations
    """
    stores = []
    
    store_names = config('CATEGORY_STORES', default='').split(',')
    
    for store_name in store_names:
        store_name = store_name.strip()
        if not store_name:
            continue
            
        root_id_key = f'CATEGORY_ROOT_ID_{store_name.upper()}'
        root_id = config(root_id_key, default=None, cast=int)
        
        if root_id:
            stores.append({
                'name': store_name,
                'root_id': root_id
            })
            logging.info(f"Configured store: {store_name} with root_id: {root_id}")
        else:
            logging.warning(f"Missing root_id configuration for store: {store_name} (expected: {root_id_key})")
    
    return stores

def main():
    """
    Main function - configure import here
    """
    try:
        helper = CategoryHelper()
        
        # === CONFIGURE IMPORT HERE ===
        
        # Option 1: Import to ALL configured stores (DEFAULT)
        stores_config = get_stores_configuration()
        
        if not stores_config:
            print("ERROR: No stores configured. Check CATEGORY_STORES environment variable.")
            return
        
        print(f"Configured stores: {[s['name'] for s in stores_config]}")
        
        result = helper.createCategoriesForMultipleStores(stores_config)
        
        print("RESULTS:")
        for store_name, stats in result['stores'].items():
            print(f"  {store_name}: {stats['created']} created, {stats['existing']} existing, {stats['errors']} errors")
        
        # Option 2: Preview categories without creating
        # result = helper.previewCategories()
        # print(f"Found {result['total_categories']} categories in {len(result['levels'])} levels")
        
        # Option 3: Import to single store (specify store name)
        # single_store_name = 'store1'  # Change this to your store name
        # single_root_id = config(f'CATEGORY_ROOT_ID_{single_store_name.upper()}', cast=int)
        # result = helper.createAllCategories(single_root_id, single_store_name)
        # print(f"{single_store_name}: Created: {result['categories_created']}, Errors: {result['errors']}")
        
        print("IMPORT COMPLETED")
            
    except KeyboardInterrupt:
        print("Import interrupted by user")
        logging.info("Import interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        logging.error(f"Error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()