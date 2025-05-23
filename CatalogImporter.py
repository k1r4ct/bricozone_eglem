
"""
Script for importing Magento attributes from mapping_attributi table
"""

import logging
import datetime
import time
from tqdm import tqdm
from lib.helper.DatabaseMappingConnectionConfig import EglemTestDbHelper
from lib.helper.MagentoAttributeHelper import MagentoAttributeHelper
from lib.helper.CatalogImporterConfigHelper import config

logging.basicConfig(
    filename=config('LOGGING_FILE', default='create_attributes.log'), 
    level=config('LOGGING_LEVEL', default='INFO'),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AttributeCreator:
    """
    Class to manage attribute creation from EglemTest to Magento
    """
    
    def __init__(self):
        self.stats = {
            'total_attributes': 0,
            'attributes_created': 0,
            'attributes_existing': 0,
            'attributes_assigned': 0,
            'errors': 0
        }
    

    def get_attributes_from_magento(self):
        """
        Retrieve attributes from mapping_attributi table
        
        Returns:
            list: List of attributes to process
        """
        print("Retrieving attributes from mapping_attributi table...")
        

        attributes = EglemTestDbHelper.getAttributesFromMapping()
        
        if not attributes:
            print("No attributes found in mapping_attributi table")
            return []
        
        print(f"Found {len(attributes)} attributes to process")
        self.stats['total_attributes'] = len(attributes)

        return attributes
    
    def create_attributes_in_magento(self, attributes):
        """
        Create attributes in Magento
        
        Args:
            attributes (list): List of attributes to create
        """
        print("\n" + "="*60)
        print("CREATING ATTRIBUTES IN MAGENTO")
        print("="*60)
        
        if not attributes:
            print("No attributes to create")
            return
        
        # Get existing attribute sets
        magento_attribute_sets = MagentoAttributeHelper.getExistingAttributeSets()
        default_set_id = config('ATTRIBUTE_DEFAULT_SET_ID', default=4, cast=int)
        
        print(f"Available attribute sets: {list(magento_attribute_sets.keys())}")
        print(f"Using default set ID: {default_set_id}")
        
        # Get existing attributes to avoid duplicates
        magento_existing_attributes  = MagentoAttributeHelper.getExistingAttributes()
        
        # Process each attribute
        for attr in tqdm(attributes, desc="Creating attributes"):
            try:
                # Create the attribute
                attribute_id, attribute_code = MagentoAttributeHelper.createAttribute(attr)
                
                if attribute_id and attribute_code:
                    # Check if it was created or already existed
                    if attribute_code in magento_existing_attributes :
                        self.stats['attributes_existing'] += 1
                        print(f"  ✓ Existing: {attribute_code}")
                    else:
                        self.stats['attributes_created'] += 1
                        print(f"  ✓ Created: {attribute_code} (ID: {attribute_id})")
                        
                        # Update ID in EglemTest if needed
                        if not attr.get('id_attribute') or attr.get('id_attribute') == 0:
                            EglemTestDbHelper.updateAttributeId(attr['id'], attribute_id)
                    
                    # Assign attribute to default set
                    if MagentoAttributeHelper.assignAttributeToSet(attribute_code, default_set_id):
                        self.stats['attributes_assigned'] += 1
                else:
                    self.stats['errors'] += 1
                    logging.error(f"Error creating attribute: {attr['original_code']}")
                
                # Small pause to avoid API overload
                time.sleep(0.1)
                
            except Exception as e:
                self.stats['errors'] += 1
                logging.error(f"Error processing attribute {attr['original_code']}: {str(e)}")
                print(f"Error in attribute {attr['original_code']}: {str(e)}")
    
    def print_summary(self):
        """
        Print operation summary
        """
        print("\n" + "="*60)
        print("OPERATION SUMMARY")
        print("="*60)
        print(f"Total attributes processed: {self.stats['total_attributes']}")
        print(f"Attributes created:         {self.stats['attributes_created']}")
        print(f"Attributes already existed: {self.stats['attributes_existing']}")
        print(f"Attributes assigned to set: {self.stats['attributes_assigned']}")
        print(f"Errors:                     {self.stats['errors']}")
        
        success_rate = ((self.stats['attributes_created'] + self.stats['attributes_existing']) / 
                       self.stats['total_attributes'] * 100) if self.stats['total_attributes'] > 0 else 0
        print(f"Success rate:               {success_rate:.1f}%")
        
        # Log summary
        logging.info("="*50)
        logging.info("ATTRIBUTE CREATION SUMMARY")
        logging.info("="*50)
        for key, value in self.stats.items():
            logging.info(f"{key}: {value}")
        logging.info(f"Success rate: {success_rate:.1f}%")
    
    def run(self):
        """
        Execute the complete attribute creation process
        """
        print("="*60)
        print("MAGENTO ATTRIBUTE CREATION SCRIPT")
        print("="*60)
        print(f"Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Verify connections
        if not self.verify_connections():
            print("Connection errors. Exiting.")
            return False
        
        # Retrieve attributes
        attributes = self.get_attributes_from_magento()
        if not attributes:
            print("No attributes to process. Exiting.")
            return False
        
        # Ask for confirmation
        response = input(f"\nProceed with creating {len(attributes)} attributes? (y/N): ")
        if response.lower() not in ['y', 'yes', 's', 'si']:
            print("Operation cancelled by user.")
            return False
        
        # Create attributes
        self.create_attributes_in_magento(attributes)
        
        # Print summary
        self.print_summary()
        
        print(f"\nCompleted: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True


def main():
    """
    Main function
    """
    try:
        creator = AttributeCreator()
        success = creator.run()
        
        if success:
            print("\n✓ Script completed successfully!")
        else:
            print("\n✗ Script terminated with errors")
            
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
        logging.info("Script interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())


if __name__ == "__main__":
    main()