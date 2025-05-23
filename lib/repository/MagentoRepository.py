import requests
import json
import mysql.connector
from decouple import config
import logging
#from lib.helper.SQLHelper import SQLHelper
from lib.connector.SQLConnector import SQLConnector

class MagentoRepository:
    """
    Repository for connectivity with Magento (API and Database)
    """

    # === Database Connection ===
    @staticmethod
    def getDbConnection():
        """
        Gets connection to Magento database
        """
        return SQLConnector(
            config('MAGENTO_DB_HOST'), 
            config('MAGENTO_DB_PORT', cast=int), 
            config('MAGENTO_DB_DATABASE'), 
            config('MAGENTO_DB_USER'), 
            config('MAGENTO_DB_PASSWORD')
        )

    @staticmethod
    def closeDbConnection(connection):
        """
        Closes database connection
        """
        return SQLConnector.close(connection)

    #TO EVALUATE
    @staticmethod
    def executeQuery(query, params=None, options={"connection": None, "close": True}):
        """
        Executes query on Magento database
        """

        return SQLConnector.executeQuery(query, params, options)