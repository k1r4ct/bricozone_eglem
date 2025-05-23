import logging
import json
import requests
from requests_oauthlib import OAuth1Session
from lib.helper.ZangooHelper import ZangooHelper
from lib.helper.MagentoHelper import CategoryHelper
from lib.helper.CatalogImporterConfigHelper import config


class CategoryHelper:
    """
    Helper for complete management of Zangoo -> Magento categories
    Uses existing helpers and saves the mapping directly in the Zangoo DB
    Fully parameterized for multiple stores
    """

    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'categories_created': 0,
            'categories_existing': 0,
            'errors': 0
        }

    # =============================================================================
    # MAGENTO API CALLS
    # =============================================================================

    @staticmethod
    def createMagentoCategory(name, parent_id):
        """Creates category in Magento using existing helper"""
        return CategoryHelper.createCategory(name, parent_id)

    # =============================================================================
    # MAPPING MANAGEMENT IN ZANGOO DB
    # =============================================================================

    def initializeCategoryMappingTable(self):
        """Initializes single mapping table in Zangoo DB for all stores"""
        try:
            connection = ZangooHelper.getConnection()
            cursor = connection.cursor()
            
            # Create single mapping table for all stores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS category_magento_mapping (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_path VARCHAR(500) NOT NULL,
                    store_name VARCHAR(100) NOT NULL,
                    magento_category_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_path_store (category_path, store_name),
                    INDEX idx_path (category_path),
                    INDEX idx_store (store_name)
                )
            """)
            
            connection.commit()
            ZangooHelper.connectionClose(connection)
            
        except Exception as e:
            logging.error(f"Error initializing mapping table: {str(e)}")

    def saveCategoryMapping(self, path, magento_category_id, store_name):
        """Saves mapping in Zangoo DB with store name"""
        try:
            connection = ZangooHelper.getConnection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO category_magento_mapping (category_path, store_name, magento_category_id)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE magento_category_id = %s
            """, (path, store_name, magento_category_id, magento_category_id))
            
            connection.commit()
            ZangooHelper.connectionClose(connection)
            
        except Exception as e:
            logging.error(f"Error saving mapping {path} for store {store_name}: {str(e)}")

    def getParentCategoryId(self, category_path, store_name):
        """Gets parent category ID from Zangoo mapping for specific store"""
        if not category_path or '/' not in category_path:
            return None
        
        try:
            connection = ZangooHelper.getConnection()
            cursor = connection.cursor()
            
            path_segments = category_path.split('/')
            parent_path = '/'.join(path_segments[:-1])
            
            cursor.execute("""
                SELECT magento_category_id 
                FROM category_magento_mapping 
                WHERE category_path = %s AND store_name = %s
            """, (parent_path, store_name))
            
            result = cursor.fetchone()
            ZangooHelper.connectionClose(connection)
            
            return result[0] if result else None
            
        except Exception as e:
            logging.error(f"Error retrieving parent for {category_path} in store {store_name}: {str(e)}")
            return None

    # =============================================================================
    # CATEGORIES MANAGEMENT
    # =============================================================================

    def getCategoriesByLevel(self, store_name):
        """Gets categories from Zangoo DB with updated query for specific store"""
        try:
            connection = ZangooHelper.getConnection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT 
                    CONCAT_WS('/', cat0.nome, cat1.nome, cat2.nome, cat3.nome) AS categories,
                    LENGTH(CONCAT_WS('/', cat0.nome, cat1.nome, cat2.nome, cat3.nome)) - 
                    LENGTH(REPLACE(CONCAT_WS('/', cat0.nome, cat1.nome, cat2.nome, cat3.nome), '/', '')) + 1 AS pathlevels,
                    SUBSTRING_INDEX(CONCAT_WS('/', cat0.nome, cat1.nome, cat2.nome, cat3.nome), '/', -1) AS leafcategory,
                    cmm.magento_category_id
                FROM categorie c
                LEFT JOIN categorie cat3 ON cat3.id = c.id
                LEFT JOIN categorie cat2 ON cat2.id = cat3.id_parent
                LEFT JOIN categorie cat1 ON cat1.id = cat2.id_parent
                LEFT JOIN categorie cat0 ON cat0.id = cat1.id_parent
                LEFT JOIN category_magento_mapping cmm ON (
                    cmm.category_path = CONCAT_WS('/', cat0.nome, cat1.nome, cat2.nome, cat3.nome) 
                    AND cmm.store_name = %s
                )
                WHERE CONCAT_WS('/', cat0.nome, cat1.nome, cat2.nome, cat3.nome) IS NOT NULL
                AND CONCAT_WS('/', cat0.nome, cat1.nome, cat2.nome, cat3.nome) != ''
                GROUP BY categories
                ORDER BY pathlevels ASC, categories ASC
            """
            
            cursor.execute(query, (store_name,))
            results = cursor.fetchall()
            
            categories_by_level = {}
            for row in results:
                level = row['pathlevels']
                if level not in categories_by_level:
                    categories_by_level[level] = []
                categories_by_level[level].append(row)
            
            ZangooHelper.connectionClose(connection)
            return categories_by_level
            
        except Exception as e:
            logging.error(f"Error retrieving categories for store {store_name}: {str(e)}")
            return {}

    def createCategoriesForLevel(self, level_categories, root_category_id, store_name):
        """Creates categories for a specific level and store"""
        created_count = 0
        
        for category_data in level_categories:
            path = category_data['categories']
            leaf_name = category_data['leafcategory']
            existing_id = category_data.get('magento_category_id')
            
            try:
                # Check if category is already mapped for this store
                if existing_id:
                    self.stats['categories_existing'] += 1
                    continue
                
                # Determine parent ID
                if category_data['pathlevels'] == 1:
                    parent_id = root_category_id
                else:
                    parent_id = self.getParentCategoryId(path, store_name)
                    if not parent_id:
                        logging.error(f"Parent category not found: {path} for store {store_name}")
                        self.stats['errors'] += 1
                        continue
                
                # Create category in Magento
                category_id = self.createMagentoCategory(leaf_name, parent_id)
                
                if category_id:
                    # Save mapping in Zangoo DB for this store
                    self.saveCategoryMapping(path, category_id, store_name)
                    created_count += 1
                    self.stats['categories_created'] += 1
                    logging.info(f"Category created: {path} (ID: {category_id}) for store {store_name}")
                else:
                    self.stats['errors'] += 1
                    logging.error(f"Error creating category: {path} for store {store_name}")
                
                self.stats['total_processed'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                logging.error(f"Error creating {path} for store {store_name}: {str(e)}")
        
        return created_count

    def createAllCategories(self, root_category_id, store_name):
        """Creates all categories processing level by level for specific store"""
        logging.info(f"Starting category creation with root_id: {root_category_id} for store: {store_name}")
        
        # Initialize mapping table
        self.initializeCategoryMappingTable()
        
        # Get categories grouped by level for this store
        categories_by_level = self.getCategoriesByLevel(store_name)
        
        if not categories_by_level:
            logging.error(f"No categories found in Zangoo for store {store_name}")
            return self.stats
        
        # Process level by level
        for level in sorted(categories_by_level.keys()):
            level_categories = categories_by_level[level]
            logging.info(f"Processing level {level}: {len(level_categories)} categories for store {store_name}")
            
            created_count = self.createCategoriesForLevel(level_categories, root_category_id, store_name)
            logging.info(f"Level {level} completed: {created_count} created for store {store_name}")
        
        logging.info(f"Creation completed for store {store_name} - Total: {self.stats['total_processed']}, "
                    f"Created: {self.stats['categories_created']}, "
                    f"Existing: {self.stats['categories_existing']}, "
                    f"Errors: {self.stats['errors']}")
        
        return self.stats

    def createCategoriesForMultipleStores(self, stores_config):
        """
        Creates categories for multiple stores using parameterized configuration
        
        Args:
            stores_config (list): List of dictionaries with store configuration
                                 [{'name': 'store1', 'root_id': 41}, {'name': 'store2', 'root_id': 292}]
        
        Returns:
            dict: Combined statistics for all stores
        """
        combined_stats = {
            'stores': {},
            'total_processed': 0
        }
        
        for store_config in stores_config:
            store_name = store_config['name']
            root_id = store_config['root_id']
            
            logging.info(f"Creating categories for store: {store_name}")
            
            # Reset stats for this store
            self.stats = {
                'total_processed': 0,
                'categories_created': 0,
                'categories_existing': 0,
                'errors': 0
            }
            
            # Create categories for this store
            store_stats = self.createAllCategories(root_id, store_name)
            
            # Add to combined stats
            combined_stats['stores'][store_name] = {
                'created': store_stats['categories_created'],
                'existing': store_stats['categories_existing'],
                'errors': store_stats['errors']
            }
            
            if combined_stats['total_processed'] == 0:
                combined_stats['total_processed'] = store_stats['total_processed']
        
        return combined_stats

    def previewCategories(self):
        """Categories preview without creating anything"""
        categories_by_level = self.getCategoriesByLevel('preview')
        
        if not categories_by_level:
            return {"success": False, "error": "No categories found"}
        
        total_categories = sum(len(categories) for categories in categories_by_level.values())
        
        preview_data = {
            "success": True,
            "total_categories": total_categories,
            "levels": {}
        }
        
        for level, categories in categories_by_level.items():
            preview_data["levels"][level] = {
                "count": len(categories),
                "sample_paths": [cat['categories'] for cat in categories[:3]]
            }
        
        return preview_data