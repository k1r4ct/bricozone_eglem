import mysql.connector
import logging
from decouple import Config, RepositoryEnv
from lib.helper.SQLHelper import SQLHelper
import os

# Load configurations from .env.import mysql.connector
import logging
from lib.helper.SQLHelper import SQLHelper
from lib.helper.CatalogImporterConfigHelper import config

class EglemTestDbHelper(SQLHelper):
    """
    Helper to manage operations on EglemTest database
    """

    @staticmethod
    def getConnection():
        """Get a connection to EglemTest database"""
        return SQLHelper.getConnection(
            config('EGLEMTEST_DB_HOST', default='127.0.0.1'), 
            config('EGLEMTEST_DB_PORT', default=3309, cast=int), 
            config('EGLEMTEST_DB_DATABASE'), 
            config('EGLEMTEST_DB_USER', default='root'), 
            config('EGLEMTEST_DB_PASSWORD', default='bcame25')
        )

    @staticmethod
    def connectionClose(connection):
        """Close database connection"""
        return SQLHelper.connectionClose(connection)

    @staticmethod
    def getAttributesFromMapping(options={"connection": None, "close": True}):
        """
        Retrieve all attributes from mapping_attributi table
        
        Returns:
            List[dict]: List of attributes with all table fields
        """
        try:
            connection = options["connection"] if options["connection"] else EglemTestDbHelper.getConnection()
            cursor = connection.cursor(dictionary=True)
            
            select_query = """
                SELECT 
                    id,
                    original_code,
                    id_attribute,
                    label,
                    normalized_code,
                    frontendInput
                FROM mapping_attributi
                ORDER BY id
            """
            
            cursor.execute(select_query)
            attributes = cursor.fetchall()
            
            logging.info(f"Retrieved {len(attributes)} attributes from mapping_attributi table")
            return attributes
            
        except Exception as ex:
            logging.error(f"Error retrieving attributes: {str(ex)}")
            return []
        
        finally:
            if options["close"]:
                EglemTestDbHelper.connectionClose(connection)

    @staticmethod
    def getAttributeByCode(attribute_code, options={"connection": None, "close": True}):
        """
        Retrieve a single attribute by code
        
        Args:
            attribute_code (str): Attribute code to search
            
        Returns:
            dict|None: Found attribute or None
        """
        try:
            connection = options["connection"] if options["connection"] else EglemTestDbHelper.getConnection()
            cursor = connection.cursor(dictionary=True)
            
            select_query = """
                SELECT 
                    id,
                    original_code,
                    id_attribute,
                    label,
                    normalized_code,
                    frontendInput
                FROM mapping_attributi
                WHERE original_code = %s OR normalized_code = %s
                LIMIT 1
            """
            
            cursor.execute(select_query, (attribute_code, attribute_code))
            attribute = cursor.fetchone()
            
            return attribute
            
        except Exception as ex:
            logging.error(f"Error retrieving attribute {attribute_code}: {str(ex)}")
            return None
        
        finally:
            if options["close"]:
                EglemTestDbHelper.connectionClose(connection)

    @staticmethod
    def updateAttributeId(mapping_id, magento_attribute_id, options={"connection": None, "close": True}):
        """
        Update the id_attribute of a record in mapping_attributi table
        
        Args:
            mapping_id (int): ID of the record in mapping table
            magento_attribute_id (int): Attribute ID in Magento
        """
        try:
            connection = options["connection"] if options["connection"] else EglemTestDbHelper.getConnection()
            cursor = connection.cursor()
            
            update_query = """
                UPDATE mapping_attributi 
                SET id_attribute = %s 
                WHERE id = %s
            """
            
            cursor.execute(update_query, (magento_attribute_id, mapping_id))
            connection.commit()
            
            logging.info(f"Updated attribute mapping ID {mapping_id} with Magento ID {magento_attribute_id}")
            
        except Exception as ex:
            logging.error(f"Error updating attribute: {str(ex)}")
        
        finally:
            if options["close"]:
                EglemTestDbHelper.connectionClose(connection)