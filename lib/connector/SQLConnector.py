import mysql.connector
from decouple import config
import logging

class SQLConnector:

    _connection = None

    def __init__(self, host, port, database, user, password):
        try:
            self._connection = mysql.connector.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                use_pure=True
            )

        except Exception as ex:
            logging.error("An exception has been thrown during the database connection: ", str(ex))

    def getConnection(self):
            return self._connection

    # close the database connection
    def close(self, connection=None):
        try:
            if connection:
                connection.close()
            else:
                self._connection.close()
        except Exception as ex:
            logging.error("An exception has been thrown during the database connection closing: ", str(ex))


    @staticmethod
    def executeQuery(query, params=None, options={"connection": None, "close": True}):
        """
        Executes query on Magento database
        """
        connection = None
        try:
            connection = options["connection"]
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
                connection.close()