import requests
import json
import mysql.connector
from decouple import config
import logging
from lib.helper.SQLHelper import SQLHelper

class MagentoConnector:
    """
    Repository for basic connectivity with Magento (API and Database)
    """

    # === API Configuration ===
    @staticmethod
    def _getHost():
        return config('MAGENTO_HOST')

    @staticmethod
    def _getToken(options={"externalToken": False, "accessToken": None}):
        if options.get("externalToken"):
            return options.get("accessToken")
        return config('MAGENTO_TOKEN')

    @staticmethod
    def _getHeaders(options={"externalToken": False, "accessToken": None}):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MagentoConnector._getToken(options)}"
        }

    # === API Calls ===
    @staticmethod
    def apiCall(method, urlPath, data=None, options={"externalToken": False, "accessToken": None}):
        """
        Executes generic API call to Magento
        """
        return requests.request(
            method.upper(),
            f"{MagentoConnector._getHost()}{urlPath}",
            headers=MagentoConnector._getHeaders(options),
            params=data if method.lower() == 'get' else None,
            json=data if method.lower() != 'get' else None,
        )

    @staticmethod
    def apiGet(endpoint, options={"externalToken": False, "accessToken": None}):
        """
        Executes GET API
        """
        response = MagentoConnector.apiCall("GET", endpoint, None, options)
        return response.json() if response.status_code == 200 else None

    @staticmethod
    def apiPost(endpoint, data, options={"externalToken": False, "accessToken": None}):
        """
        Executes POST API
        """
        response = MagentoConnector.apiCall("POST", endpoint, data, options)
        return response.json() if response.status_code in [200, 201] else None

    @staticmethod
    def apiPut(endpoint, data, options={"externalToken": False, "accessToken": None}):
        """
        Executes PUT API
        """
        response = MagentoConnector.apiCall("PUT", endpoint, data, options)
        return response.json() if response.status_code == 200 else None

    # === Database Connection ===
    @staticmethod
    def getDbConnection():
        """
        Gets connection to Magento database
        """
        return SQLHelper.getConnection(
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
        return SQLHelper.connectionClose(connection)

    @staticmethod
    def executeQuery(query, params=None, options={"connection": None, "close": True}):
        """
        Executes query on Magento database
        """
        try:
            connection = options["connection"] if options["connection"] else MagentoConnector.getDbConnection()
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            
            if not options["connection"]:
                connection.commit()
            
            return result
            
        except Exception as ex:
            logging.error(f"Error executing query: {str(ex)}")
            return None
        finally:
            if options["close"]:
                MagentoConnector.closeDbConnection(connection)