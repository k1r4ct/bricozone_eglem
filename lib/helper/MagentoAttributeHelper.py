import requests
import json
import logging
import time
from lib.helper.MagentoHelper import MagentoHelper
from lib.helper.CatalogImporterConfigHelper import config

class MagentoAttributeHelper(MagentoHelper):
    """
    Specialized helper for managing attributes in Magento
    """

    @staticmethod
    def _getHost():
        return config('MAGENTO_HOST')

    @staticmethod
    def _getToken():
        return config('MAGENTO_TOKEN')

    @staticmethod
    def _getHeaders():
        """
        Get headers for Bearer Token authentication
        """
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MagentoAttributeHelper._getToken()}"
        }

    @staticmethod
    def _apiCall(method, endpoint, data=None):
        """
        Execute authenticated API calls to Magento using Bearer Token
        
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            endpoint (str): API endpoint (without base URL)
            data (dict): Data to send (for POST/PUT)
            
        Returns:
            requests.Response|None: Response object or None if error
        """
        url = f"{MagentoAttributeHelper._getHost()}/rest/default/V1/{endpoint}"
        headers = MagentoAttributeHelper._getHeaders()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
            
        except Exception as e:
            logging.error(f"Error in API call {method} {endpoint}: {str(e)}")
            return None

    @staticmethod
    def getExistingAttributes():
        """
        Retrieve all existing attributes from Magento
        
        Returns:
            dict: Dictionary with attribute_code as key and attribute data as value
        """
        response = MagentoAttributeHelper._apiCall("GET", "products/attributes?searchCriteria[pageSize]=500")
        
        if response and response.status_code == 200:
            data = response.json()
            if 'items' in data:
                attributes = {item['attribute_code']: item for item in data['items']}
                logging.info(f"Found {len(attributes)} existing attributes in Magento")
                return attributes
        
        logging.warning("No attributes found or error retrieving them")
        return {}

    @staticmethod
    def getExistingAttributeSets():
        """
        Retrieve all existing attribute sets from Magento
        
        Returns:
            dict: Dictionary with set name as key and ID as value
        """
        response = MagentoAttributeHelper._apiCall("GET", "products/attribute-sets/sets/list?searchCriteria=0")
        
        if response and response.status_code == 200:
            data = response.json()
            if 'items' in data:
                attribute_sets = {item['attribute_set_name']: item['attribute_set_id'] for item in data['items']}
                logging.info(f"Found {len(attribute_sets)} existing attribute sets")
                return attribute_sets
        
        logging.warning("No attribute sets found or error retrieving them")
        return {}

    @staticmethod
    def createAttribute(attribute_data):
        """
        Create a new attribute in Magento using the normalized_code
        
        Args:
            attribute_data (dict): Attribute data with fields:
                - original_code: Original code (for logging)
                - label: Label to display
                - normalized_code: Normalized code to use as attribute_code
        
        Returns:
            tuple: (attribute_id, attribute_code) or (None, None) if error
        """
        original_code = attribute_data.get('original_code', '')
        label = attribute_data.get('label', '')
        normalized_code = attribute_data.get('normalized_code', '')
        frontendInput = attribute_data.get('frontendInput', 'text')

        if not normalized_code:
            logging.error(f"Missing normalized code for attribute {original_code}")
            return None, None
        
        # Use normalized_code as attribute_code
        attribute_code = normalized_code
        front_end_input = frontendInput
        
        # Check if attribute already exists
        existing_attributes = MagentoAttributeHelper.getExistingAttributes()
        if attribute_code in existing_attributes:
            existing_attr = existing_attributes[attribute_code]
            logging.info(f"Attribute already exists: {attribute_code}")
            return existing_attr.get('attribute_id'), attribute_code
        
        # Data for attribute creation
        attribute_request = {
            "attribute": {
                "attributeCode": attribute_code,
                "frontendInput": front_end_input,
                "entityTypeId": config('ATTRIBUTE_ENTITY_TYPE_ID', default=4, cast=int),
                "isRequired": False,
                "isUnique": False,
                "isSearchable": 1,
                "isVisibleInAdvancedSearch": 1,
                "isComparable": 1,
                "isFilterable": 1,
                "isFilterableInSearch": 1,
                "isUsedForPromoRules": 1,
                "isVisibleOnFront": 1,
                "usedInProductListing": 1,
                "frontendLabels": [
                    {
                        "storeId": config('MAGENTO_STORE_ID', default=0, cast=int),
                        "label": label or original_code
                    }
                ]
            }
        }
        
        logging.info(f"Creating attribute: {attribute_code} (Original: {original_code}, Label: {label})")
        
        response = MagentoAttributeHelper._apiCall("POST", "products/attributes", attribute_request)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'attribute_id' in response_data:
                attribute_id = response_data['attribute_id']
                logging.info(f"Attribute created successfully: {attribute_code} (ID: {attribute_id})")
                return attribute_id, attribute_code
        
        # Log error
        if response:
            logging.error(f"Error creating attribute {attribute_code}: Status {response.status_code}, Response: {response.text}")
        else:
            logging.error(f"Error creating attribute {attribute_code}: No response from server")
        
        return None, None

    @staticmethod
    def getAttributeGroupsForSet(attribute_set_id):
        """
        Get attribute groups for a specific set
        
        Args:
            attribute_set_id (int): Attribute set ID
            
        Returns:
            dict: Dictionary with group name as key and ID as value
        """
        filter_q = (
            f"searchCriteria[filter_groups][0][filters][0][field]=attribute_set_id&"
            f"searchCriteria[filter_groups][0][filters][0][value]={attribute_set_id}&"
            f"searchCriteria[filter_groups][0][filters][0][condition_type]=eq"
        )
        
        response = MagentoAttributeHelper._apiCall("GET", f"products/attribute-sets/groups/list?{filter_q}")
        
        if response and response.status_code == 200:
            data = response.json()
            if 'items' in data and data['items']:
                groups = {}
                for group in data['items']:
                    group_name = group.get('attribute_group_name')
                    group_id = group.get('attribute_group_id')
                    if group_name and group_id:
                        groups[group_name] = group_id
                return groups
        
        return {}

    @staticmethod
    def assignAttributeToSet(attribute_code, attribute_set_id, group_name="Product Details"):
        """
        Assign an attribute to an attribute set
        
        Args:
            attribute_code (str): Attribute code
            attribute_set_id (int): Attribute set ID
            group_name (str): Group name (default: "Product Details")
            
        Returns:
            bool: True if success, False otherwise
        """
        # Get groups for this set
        groups = MagentoAttributeHelper.getAttributeGroupsForSet(attribute_set_id)
        
        if not groups:
            logging.error(f"No groups found for set {attribute_set_id}")
            return False
        
        # Find the correct group
        group_id = None
        target_groups = [group_name, "Product Details", "product-details", "product_details", "Product-Details"]
        
        for target in target_groups:
            if target in groups:
                group_id = groups[target]
                break
        
        # If not found, use the first available group
        if group_id is None and groups:
            group_id = next(iter(groups.values()))
            logging.warning(f"Group '{group_name}' not found, using first available")
        
        if group_id is None:
            logging.error(f"No group available for set {attribute_set_id}")
            return False
        
        # Assignment data
        assignment_data = {
            "attributeSetId": attribute_set_id,
            "attributeGroupId": group_id,
            "attributeCode": attribute_code,
            "sortOrder": 0
        }
        
        response = MagentoAttributeHelper._apiCall("POST", "products/attribute-sets/attributes", assignment_data)
        
        if response and response.status_code == 200:
            logging.info(f"Attribute {attribute_code} assigned to set {attribute_set_id} in group {group_id}")
            return True
        else:
            if response:
                logging.error(f"Error assigning attribute {attribute_code}: {response.status_code} - {response.text}")
            return False

    @staticmethod
    def verifyMagentoConnection():
        """
        Verify connection with Magento API
        
        Returns:
            bool: True if connection is ok, False otherwise
        """
        logging.info("Verifying Magento API connection...")
        
        response = MagentoAttributeHelper._apiCall("GET", "store/storeConfigs")
        
        if response and response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                store_info = data[0]
                store_name = store_info.get('store_name', 'Unknown store')
                logging.info(f"Magento connection successful: {store_name}")
                return True
        
        logging.error("Error connecting to Magento. Check URL and credentials.")
        return False