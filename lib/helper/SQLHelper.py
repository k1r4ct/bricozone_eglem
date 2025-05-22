import mysql.connector
from decouple import config
import logging

class SQLHelper():

    def getConnection(host, port, database, user, password):
        try:
            connection = mysql.connector.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                use_pure=True
            )

        except Exception as ex:
            logging.error("An exception has been thrown during the database connection: ", str(ex))

        finally:
            return connection

    # close the database connection
    def connectionClose(connection):
        try:
            if connection:
                connection.close()

        except Exception as ex:
            logging.error("An exception has been thrown during the database connection closing: ", str(ex))