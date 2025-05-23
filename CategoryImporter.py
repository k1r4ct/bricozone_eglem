#!/usr/bin/env python3
"""
CategoryImporter.py
Import categories into Magento from Zangoo database
"""

import logging
from lib.helper.CategoryImporterManagerHelper import CategoryImportManager
from lib.helper.CatalogImporterConfigHelper import config

# Logging configuration
logging.basicConfig(
    filename=config('LOGGING_FILE', default='category_import.log'),
    level=config('LOGGING_LEVEL', default='INFO'),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """
    Main function - configure import here
    """
    try:
        manager = CategoryImportManager()
        
        # === CONFIGURE IMPORT HERE ===
        
        # Option 1: Import to BOTH Bricozone and Zangoo roots (DEFAULT)
        result = manager.import_to_both_roots(
            bricozone_root_id=None,  # Uses CATEGORY_ROOT_ID_BRICOZONE from env
            zangoo_root_id=None,     # Uses CATEGORY_ROOT_ID_ZANGOO from env
            verify_connections=False
        )
        
        # Option 2: Preview categories without creating
        # result = manager.preview_categories()
        
        # Option 3: Import to single root (original behavior)
        # result = manager.import_to_single_root(
        #     root_category_id=None,  # Uses configured root from env
        #     verify_connections=False
        # )
        
        if result["success"]:
            print("\nIMPORT COMPLETED SUCCESSFULLY!")
        else:
            print("\nIMPORT FAILED!")
            
    except KeyboardInterrupt:
        print("\n\nImport interrupted by user")
        logging.info("Import interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())


if __name__ == "__main__":
    main()