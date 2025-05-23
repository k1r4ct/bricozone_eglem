import requests
import json
import logging
import time
import re
import unidecode
from requests_oauthlib import OAuth1Session
from lib.helper.MagentoHelper import MagentoHelper
from lib.helper.CatalogImporterConfigHelper import config

class MagentoCategoryHelper(MagentoHelper):
    """
    Helper specialized for managing categories in Magento using OAuth from environment
    """

    @staticmethod
    def _getApiConfig():
        """Get OAuth configuration from environment variables"""
        return {
            "consumer_key": config('MAGENTO_CONSUMER_KEY'),
            "consumer_secret": config('MAGENTO_CONSUMER_SECRET'),
            "access_token": config('MAGENTO_ACCESS_TOKEN'),
            "access_token_secret": config('MAGENTO_ACCESS_TOKEN_SECRET')
        }

    @staticmethod
    def _getBaseUrl():
        """Get base URL from environment"""
        host = config('MAGENTO_HOST')
        return f"{host}/rest/default/V1"

    @staticmethod
    def _getOAuthSession():
        """Create OAuth session using environment configuration"""
        api_config = MagentoCategoryHelper._getApiConfig()
        return OAuth1Session(
            client_key=api_config["consumer_key"],
            client_secret=api_config["consumer_secret"],
            resource_owner_key=api_config["access_token"],
            resource_owner_secret=api_config["access_token_secret"],
            signature_method='HMAC-SHA256',
            signature_type='AUTH_HEADER'
        )

    @staticmethod
    def api_get(endpoint):
        """
        Execute a GET request using OAuth from environment
        """
        base_url = MagentoCategoryHelper._getBaseUrl()
        url = f"{base_url}/{endpoint}"
        oauth_session = MagentoCategoryHelper._getOAuthSession()
        
        try:
            response = oauth_session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"API GET error: {url} - Status {response.status_code}")
                logging.error(f"Response: {response.text}")
                return None
        except Exception as error:
            logging.error(f"Exception in API GET: {url} - {str(error)}")
            return None

    @staticmethod
    def api_post(endpoint, data):
        """
        Execute a POST request using OAuth from environment
        """
        base_url = MagentoCategoryHelper._getBaseUrl()
        url = f"{base_url}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        oauth_session = MagentoCategoryHelper._getOAuthSession()
        
        try:
            response = oauth_session.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logging.error(f"API POST error: {url} - Status {response.status_code}")
                logging.error(f"Response: {response.text}")
                return None
        except Exception as error:
            logging.error(f"Exception in API POST: {url} - {str(error)}")
            return None

    @staticmethod
    def verifyMagentoConnection():
        """
        Verify connection with Magento API
        
        Returns:
            bool: True if connection is OK
        """
        logging.info("Verifying Magento API connection...")
        
        response = MagentoCategoryHelper.api_get("store/storeConfigs")
        
        if response:
            if isinstance(response, list) and len(response) > 0:
                store_info = response[0]
                store_name = store_info.get('store_name', 'Unknown store')
            else:
                store_name = "Unknown store"
            
            logging.info(f"Magento connection successful: {store_name}")
            return True
        else:
            logging.error("Error connecting to Magento. Check URL and credentials.")
            return False

    @staticmethod
    def getExistingCategories():
        """
        Retrieve all existing categories from Magento
        
        Returns:
            dict: Map path -> category_id
        """
        logging.info("Retrieving existing categories from Magento...")
        
        response = MagentoCategoryHelper.api_get("categories")
        
        categories_map = {}
        
        if response:
            def extract_categories(category, parent_path=""):
                """Recursive function to extract all category paths"""
                name = category.get('name', '')
                category_id = category.get('id')
                
                # Build full path
                current_path = f"{parent_path}/{name}" if parent_path else name
                current_path = current_path.strip('/')
                
                if category_id and name:
                    categories_map[current_path] = category_id
                
                # Process child categories
                if 'children_data' in category:
                    for child in category['children_data']:
                        extract_categories(child, current_path)
            
            # Start extraction from root category
            extract_categories(response)
            
        logging.info(f"Found {len(categories_map)} existing categories in Magento")
        return categories_map

    @staticmethod
    def createCategory(name, parent_id, url_key=None):
        """
        Create a new category in Magento
        
        Args:
            name (str): Category name
            parent_id (int): Parent category ID
            url_key (str, optional): Custom URL key
            
        Returns:
            int|None: Created category ID or None if error
        """
        # Generate url_key if not provided
        if not url_key:
            url_key = MagentoCategoryHelper._generateUrlKey(name)
        
        category_data = {
            "category": {
                "parent_id": parent_id,
                "name": name,
                "is_active": True,
                "include_in_menu": True,
                "custom_attributes": [
                    {
                        "attribute_code": "url_key",
                        "value": url_key
                    }
                ]
            }
        }
        
        logging.info(f"Creating category: '{name}' (parent_id: {parent_id})")
        
        response = MagentoCategoryHelper.api_post("categories", category_data)
        
        if response and 'id' in response:
            category_id = response.get('id')
            logging.info(f"Category created successfully: '{name}' (ID: {category_id})")
            return category_id
        else:
            logging.error(f"Error creating category '{name}': No response from server")
            return None

    @staticmethod
    def _generateUrlKey(name):
        """
        Generate a valid URL key from category name
        
        Args:
            name (str): Category name
            
        Returns:
            str: Clean URL key
        """
        # if not name:
        #     return "category"
        
        # Remove accents and convert to ASCII
        url_key = unidecode.unidecode(name)
        
        # # Convert to lowercase
        # url_key = url_key.lower()
        
        # # Replace spaces and special characters with hyphens
        # url_key = re.sub(r'[^a-z0-9\-]', '-', url_key)
        
        # # Remove multiple hyphens
        # url_key = re.sub(r'-+', '-', url_key)
        
        # # Remove leading and trailing hyphens
        # url_key = url_key.strip('-')
        
        # # Ensure it's not empty
        # if not url_key:
        #     url_key = "category"
        
        return url_key

    @staticmethod
    def createCategoryPath(category_path, root_category_id):
        """
        Create an entire category path, creating missing categories
        
        Args:
            category_path (str): Category path (e.g., "Home/Bathroom/Accessories")
            root_category_id (int): Root category ID
            
        Returns:
            dict: Operation result with success, error, created_categories, etc.
        """
        if not category_path or not category_path.strip():
            return {"success": False, "error": "Empty category path"}
        
        segments = [segment.strip() for segment in category_path.split('/') if segment.strip()]
        
        if not segments:
            return {"success": False, "error": "No valid segments in path"}
        
        existing_categories = MagentoCategoryHelper.getExistingCategories()
        
        current_parent_id = root_category_id
        current_path = ""
        created_categories = []
        
        for segment in segments:
            # Build progressive path
            current_path = f"{current_path}/{segment}" if current_path else segment
            
            # Check if category already exists
            if current_path in existing_categories:
                current_parent_id = existing_categories[current_path]
                logging.debug(f"Existing category found: '{current_path}' (ID: {current_parent_id})")
            else:
                # Create category
                category_id = MagentoCategoryHelper.createCategory(segment, current_parent_id)
                
                if category_id:
                    current_parent_id = category_id
                    created_categories.append({
                        "name": segment,
                        "path": current_path,
                        "id": category_id
                    })
                    logging.info(f"Category created: '{current_path}' (ID: {category_id})")
                    
                    # Update existing categories dictionary
                    existing_categories[current_path] = category_id
                else:
                    return {
                        "success": False, 
                        "error": f"Cannot create category '{segment}' in path '{current_path}'",
                        "created_categories": created_categories
                    }
            
            # Small pause to avoid API overload
            time.sleep(0.1)
        
        return {
            "success": True,
            "final_category_id": current_parent_id,
            "created_categories": created_categories,
            "path": category_path
        }