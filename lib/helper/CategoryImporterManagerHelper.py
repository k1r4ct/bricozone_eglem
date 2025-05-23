import logging
import datetime
from tqdm import tqdm
from lib.helper.MagentoCategoryHelper import MagentoCategoryHelper
from utils.magentoCatalogImporter.CategoryPathsUtils import CategoryPathUtils
from lib.helper.ZangooHelper import ZangooDbHelper
from lib.helper.CatalogImporterConfigHelper import config

class CategoryImportManager:
    """
    Manager class for handling category import operations
    """
    
    def __init__(self):
        self.stats = {
            'total_paths_found': 0,
            'categories_created_bricozone': 0,
            'categories_created_zangoo': 0,
            'categories_existing_bricozone': 0,
            'categories_existing_zangoo': 0,
            'errors_bricozone': 0,
            'errors_zangoo': 0,
            'db_categories_found': 0
        }
    
    def import_to_both_roots(self, bricozone_root_id=None, zangoo_root_id=None, verify_connections=False):
        """
        Import categories to both Bricozone and Zangoo root categories
        
        Args:
            bricozone_root_id (int, optional): Bricozone root category ID
            zangoo_root_id (int, optional): Zangoo root category ID
            verify_connections (bool): Whether to verify connections before starting
            
        Returns:
            dict: Import result
        """
        print("=" * 60)
        print("IMPORTING CATEGORIES TO BOTH ROOT CATEGORIES")
        print("=" * 60)
        print(f"Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Set default root IDs
        if bricozone_root_id is None:
            bricozone_root_id = config('CATEGORY_ROOT_ID_BRICOZONE', default=41, cast=int)
        if zangoo_root_id is None:
            zangoo_root_id = config('CATEGORY_ROOT_ID_ZANGOO', default=292, cast=int)
        
        print(f"Bricozone root category ID: {bricozone_root_id}")
        print(f"Zangoo root category ID: {zangoo_root_id}")
        
        # Verify connections if requested
        if verify_connections:
            if not self._verify_connections():
                return {"success": False, "stats": self.stats}
        
        # Extract paths from Zangoo database
        print("Extracting categories from Zangoo database...")
        category_paths = ZangooDbHelper.getCategoryPaths()
        
        if not category_paths:
            print("WARNING: No categories found in Zangoo database")
            return {"success": True, "stats": self.stats}
        
        self.stats['db_categories_found'] = len(category_paths)
        print(f"Found {len(category_paths)} categories in Zangoo database")
        
        # Validate and sort paths
        valid_paths = CategoryPathUtils.validatePaths(category_paths)
        sorted_paths = CategoryPathUtils.sortPathsByDepth(valid_paths)
        
        self.stats['total_paths_found'] = len(sorted_paths)
        print(f"Valid paths to process: {len(sorted_paths)}")
        
        # Import to Bricozone root
        print(f"\n Creating categories under Bricozone root (ID: {bricozone_root_id})...")
        self._create_categories_for_root(sorted_paths, bricozone_root_id, "bricozone")
        
        # Import to Zangoo root
        print(f"\n Creating categories under Zangoo root (ID: {zangoo_root_id})...")
        self._create_categories_for_root(sorted_paths, zangoo_root_id, "zangoo")
        
        # Print results
        self._print_stats()
        
        print(f"Completed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {"success": True, "stats": self.stats}
    
    def import_to_single_root(self, root_category_id=None, verify_connections=False):
        """
        Import categories to a single root category (original behavior)
        
        Args:
            root_category_id (int, optional): Root category ID
            verify_connections (bool): Whether to verify connections
            
        Returns:
            dict: Import result
        """
        print("=" * 60)
        print("IMPORTING CATEGORIES FROM ZANGOO DATABASE")
        print("=" * 60)
        print(f"Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get root category ID
        if root_category_id is None:
            root_category_id = CategoryPathUtils.getConfiguredRootId()
        
        print(f"Magento root category ID: {root_category_id}")
        
        # Verify connections if requested
        if verify_connections:
            if not self._verify_connections():
                return {"success": False, "stats": self.stats}
        
        # Extract paths from Zangoo database
        print("Extracting categories from Zangoo database...")
        category_paths = ZangooDbHelper.getCategoryPaths()
        
        if not category_paths:
            print("WARNING: No categories found in Zangoo database")
            return {"success": True, "stats": self.stats}
        
        self.stats['db_categories_found'] = len(category_paths)
        print(f"Found {len(category_paths)} categories in Zangoo database")
        
        # Validate and sort paths
        valid_paths = CategoryPathUtils.validatePaths(category_paths)
        sorted_paths = CategoryPathUtils.sortPathsByDepth(valid_paths)
        
        self.stats['total_paths_found'] = len(sorted_paths)
        print(f"Valid paths to process: {len(sorted_paths)}")
        
        # Create categories
        self._create_categories_for_root(sorted_paths, root_category_id, "single")
        
        # Print results
        self._print_stats()
        
        print(f"Completed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {"success": True, "stats": self.stats}
    
    def preview_categories(self):
        """
        Preview categories that would be imported (without creating anything)
        
        Returns:
            dict: Information about categories
        """
        print("=" * 60)
        print("CATEGORY PREVIEW FROM ZANGOO DATABASE")
        print("=" * 60)
        
        # Test database connection
        print("Testing Zangoo database connection...")
        if not ZangooDbHelper.testConnection():
            print("ERROR: Cannot connect to Zangoo database")
            return {"success": False}
        
        print("Database connection OK")
        
        # Count total categories
        total_count = ZangooDbHelper.getCategoriesCount()
        print(f"Total categories in database: {total_count}")
        
        # Extract categories
        category_paths = ZangooDbHelper.getCategoryPaths()
        
        if not category_paths:
            print("No categories found")
            return {"success": True, "paths": []}
        
        # Validate and sort
        valid_paths = CategoryPathUtils.validatePaths(category_paths)
        sorted_paths = CategoryPathUtils.sortPathsByDepth(valid_paths)
        
        print(f"Valid paths found: {len(sorted_paths)}")
        
        # Group by level
        levels = {}
        for path in sorted_paths:
            level = len(path.split('/'))
            if level not in levels:
                levels[level] = []
            levels[level].append(path)
        
        print("\nCategories by level:")
        for level in sorted(levels.keys()):
            print(f"  Level {level}: {len(levels[level])} categories")
        
        return {
            "success": True, 
            "paths": sorted_paths,
            "total_db_categories": total_count,
            "valid_paths": len(sorted_paths),
            "levels": levels
        }
    
    def _verify_connections(self):
        """
        Verify both Zangoo database and Magento API connections
        
        Returns:
            bool: True if both connections are OK
        """
        print("Verifying connections...")
        
        # Test Zangoo database
        print("Testing Zangoo database connection...")
        if not ZangooDbHelper.testConnection():
            print("ERROR: Cannot connect to Zangoo database")
            return False
        print("Zangoo database connection OK")
        
        # Test Magento API
        print("Testing Magento API connection...")
        if not MagentoCategoryHelper.verifyMagentoConnection():
            print("ERROR: Cannot connect to Magento API")
            return False
        print("Magento API connection OK")
        
        return True
    
    def _create_categories_for_root(self, sorted_paths, root_category_id, root_name):
        """
        Create categories under a specific root
        
        Args:
            sorted_paths (list): Sorted list of paths
            root_category_id (int): Root category ID
            root_name (str): Root name for stats tracking (bricozone/zangoo/single)
        """
        for path in tqdm(sorted_paths, desc=f"Creating categories for {root_name}"):
            try:
                result = MagentoCategoryHelper.createCategoryPath(path, root_category_id)
                
                if result["success"]:
                    created_count = len(result.get("created_categories", []))
                    if created_count > 0:
                        if root_name == "bricozone":
                            self.stats['categories_created_bricozone'] += created_count
                        elif root_name == "zangoo":
                            self.stats['categories_created_zangoo'] += created_count
                        else:
                            self.stats['categories_created_bricozone'] += created_count 
                        
                        logging.info(f"Path created under {root_name}: {path} - {created_count} new categories")
                    else:
                        if root_name == "bricozone":
                            self.stats['categories_existing_bricozone'] += 1
                        elif root_name == "zangoo":
                            self.stats['categories_existing_zangoo'] += 1
                        else:
                            self.stats['categories_existing_bricozone'] += 1  # fallback
                        
                        logging.debug(f"Existing path under {root_name}: {path}")
                else:
                    if root_name == "bricozone":
                        self.stats['errors_bricozone'] += 1
                    elif root_name == "zangoo":
                        self.stats['errors_zangoo'] += 1
                    else:
                        self.stats['errors_bricozone'] += 1  
                    
                    error_msg = result.get("error", "Unknown error")
                    logging.error(f"Error creating path {path} under {root_name}: {error_msg}")
                    
            except Exception as e:
                if root_name == "bricozone":
                    self.stats['errors_bricozone'] += 1
                elif root_name == "zangoo":
                    self.stats['errors_zangoo'] += 1
                else:
                    self.stats['errors_bricozone'] += 1  
                
                logging.error(f"Exception during path creation {path} under {root_name}: {str(e)}")
    
    def _print_stats(self):
        """
        Print final statistics
        """
        print("\n" + "=" * 60)
        print("IMPORT STATISTICS")
        print("=" * 60)
        print(f"Categories found in DB:           {self.stats['db_categories_found']}")
        print(f"Valid paths processed:            {self.stats['total_paths_found']}")
        
        # Bricozone stats
        bricozone_total = (self.stats['categories_created_bricozone'] + 
                          self.stats['categories_existing_bricozone'])
        print(f"\n BRICOZONE ROOT:")
        print(f"  Categories created:             {self.stats['categories_created_bricozone']}")
        print(f"  Categories already existing:    {self.stats['categories_existing_bricozone']}")
        print(f"  Errors:                         {self.stats['errors_bricozone']}")
        
        # Zangoo stats
        zangoo_total = (self.stats['categories_created_zangoo'] + 
                       self.stats['categories_existing_zangoo'])
        print(f"\n ZANGOO ROOT:")
        print(f"  Categories created:             {self.stats['categories_created_zangoo']}")
        print(f"  Categories already existing:    {self.stats['categories_existing_zangoo']}")
        print(f"  Errors:                         {self.stats['errors_zangoo']}")
        
        # Overall success rate
        total_operations = self.stats['total_paths_found'] * 2  # Due to dual import
        total_errors = self.stats['errors_bricozone'] + self.stats['errors_zangoo']
        
        success_rate = 0
        if total_operations > 0:
            success_rate = ((total_operations - total_errors) / total_operations * 100)
        
        print(f"\nOverall success rate:             {success_rate:.1f}%")