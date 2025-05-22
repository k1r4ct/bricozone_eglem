import mysql.connector
from decouple import config
import logging
from lib.helper.SQLHelper import SQLHelper

# related db tables
class BorderDbHelper(SQLHelper):

    @staticmethod
    def getConnection():
        return SQLHelper.getConnection(config('MYSQL_HOST'), config('MYSQL_PORT', cast=int), config('MYSQL_DB'), config('MYSQL_USER'), config('MYSQL_PASSWORD'))

    @staticmethod
    def connectionClose(connection):
        return SQLHelper.connectionClose(connection)

    @staticmethod
    def insertProductHistory(sku, id_eglem, price, quantity, updateStatus, jobUuid, options={"connection":None, "close":True}):
        try:
            connection = options["connection"] if options["connection"] else BorderDbHelper.getConnection()
            cursor = connection.cursor()
            insertQuery = """
                INSERT INTO product_history (
                    sku,
                    id_eglem,
                    price,
                    quantity,
                    status,
                    jobuuid
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """
            data = (sku, id_eglem, price, quantity, updateStatus, jobUuid)
            cursor.execute(insertQuery, data)
            connection.commit()

        except Exception as ex:
            logging.error("An exception has been thrown during the insertion into database: ", str(ex))

        finally:
            if options["close"]:
                BorderDbHelper.connectionClose(connection)

    @staticmethod
    def insertProductsHistory(productsList, updateStatus, jobUuid, options={"connection":None, "close":True}):
        try:
            connection = options["connection"] if options["connection"] else BorderDbHelper.getConnection()
            cursor = connection.cursor()

            row_data = [
                (product['sku'], product['id_eglem'], product['quantity'], product['price'], updateStatus, jobUuid)
                for product in productsList
            ]
            insertQuery = """
                INSERT INTO product_history (
                    sku,
                    id_eglem,
                    quantity,
                    price,
                    status,
                    jobuuid
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """
            cursor.executemany(insertQuery, row_data)
            connection.commit()

        except Exception as ex:
            logging.error("An exception has been thrown during the insertion into database: ", str(ex))

        finally:
            if options["close"]:
                BorderDbHelper.connectionClose(connection)

    # SQL SELECT to retrieve all the jobuuid with pending values from product_history table
    @staticmethod
    def getProductHistoryStatus(status, options={"connection":None,"close":True}):
        try:
            connection = options["connection"] if options["connection"] else SQLHelper.getConnection()
            cursor = connection.cursor()
            selectQuery = f"SELECT DISTINCT jobuuid FROM product_history ph WHERE ph.status='{status}'"
            cursor.execute(selectQuery)
            queryResult = cursor.fetchall()
        except Exception as ex:
            logging.error(f"An exception has been thrown during the retrieval of products with status={status}: ", str(ex))
        
        finally:
            if options["close"]:
                SQLHelper.connectionClose(connection)
            return queryResult
        

    # SQL insertion into product_history table (by direct update or bulk operation)
    @staticmethod
    def updateProductHistoryBulk(updateStatusList, options={"connection":None,"close":True}):
        try:
            connection = options["connection"] if options["connection"] else SQLHelper.getConnection()
            cursor = connection.cursor()
            # Cycle through each update status in the list
            for updateStatus in updateStatusList:
                 # Construct the SQL query for each item in the list
                inserQuery = f"UPDATE product_history SET status='{updateStatus['status']}', timestamp=CURRENT_TIMESTAMP WHERE sku='{updateStatus['sku']}' AND jobuuid='{updateStatus['bulk_uuid']}'"
                cursor.execute(inserQuery)
            if not options["connection"]:
                connection.commit()

        except Exception as ex:
            logging.error("An exception has been thrown during the bulk update into database: ", str(ex))

        finally:
            if options["close"]:
                SQLHelper.connectionClose(connection)
        

    # SQL insertion into order_history table (by direct update or bulk operation)
    @staticmethod
    def insertOrderHistory(orderList, updateStatus, jobuuid=None, options={"connection":None, "close":True}):
        try:
            connection = options["connection"] if options["connection"] else SQLHelper.getConnection()
            cursor = connection.cursor()
            if not jobuuid:
                row_data = ", ".join([f"('{order['increment_id']}', '{order['status']}', 'processing', '{updateStatus}')" for order in orderList])
                insertQuery = f"INSERT INTO order_history (increment_id, old_order_status, order_status, status) VALUES {row_data}"
                cursor.execute(insertQuery)
            else:
                row_data = ", ".join([f"('{order['increment_id']}', '{order['status']}', 'processing', '{updateStatus}', '{jobuuid}')" for order in orderList])
                insertQuery = f"INSERT INTO order_history (increment_id, old_order_status, order_status, status, jobuuid) VALUES {row_data}"
                cursor.execute(insertQuery)
            if not options["connection"]:
                connection.commit()

        except Exception as ex:
            logging.error("An exception has been thrown during the insertion into database: ", str(ex))

        finally:
            if options["close"]:
                SQLHelper.connectionClose(connection)

    # SQL SELECT to retrieve all the jobuuid with pending values from order_history table
    @staticmethod
    def getOrderHistoryStatus(status, options={"connection":None,"close":True}):
        try:
            connection = options["connection"] if options["connection"] else SQLHelper.getConnection()
            cursor = connection.cursor()
            selectQuery = f"SELECT DISTINCT jobuuid FROM order_history oh WHERE oh.status='{status}'"
            cursor.execute(selectQuery)
            queryResult = cursor.fetchall()
        except Exception as ex:
            logging.error(f"An exception has been thrown during the retrieval of products with status={status}: ", str(ex))
        
        finally:
            if options["close"]:
                SQLHelper.connectionClose(connection)
            return queryResult
        

    # SQL insertion into product_history table (by direct update or bulk operation)
    @staticmethod
    def updateOrderHistoryBulk(updateStatusList, options={"connection":None,"close":True}):
        try:
            connection = options["connection"] if options["connection"] else SQLHelper.getConnection()
            cursor = connection.cursor()
            # Cycle through each update status in the list
            for updateStatus in updateStatusList:
                 # Construct the SQL query for each item in the list
                insertQuery = f"UPDATE order_history SET status='{updateStatus['status']}', timestamp=CURRENT_TIMESTAMP WHERE increment_id='{updateStatus['increment_id']}' AND jobuuid='{updateStatus['bulk_uuid']}'"
                cursor.execute(insertQuery)
            if not options["connection"]:
                connection.commit()

        except Exception as ex:
            logging.error("An exception has been thrown during the bulk update into database: ", str(ex))

        finally:
            if options["close"]:
                SQLHelper.connectionClose(connection)


    # SQL insertion into creditmemo_history table 
    @staticmethod
    def insertCreditmemoHistory(creditmemo, options={"connection":None, "close":True}):
        # TODO: check the condition that occurs when a magento call stops with an exception, due to an error into host call
        try:
            connection = options["connection"] if options["connection"] else SQLHelper.getConnection()
            cursor = connection.cursor()
            
            row_data = ", ".join([f"('{creditmemo['creditmemo_id']}', '{item['item_sku']}', {item['id_eglem']}, {item['item_cost']}, {item['quantity_refunded']}, {creditmemo['total_cost']}, '{creditmemo['order_id']}', '{creditmemo['shipping_address']}')" for item in creditmemo['items']])
            # TODO: check if insertion has to be made only when credit['creditmemo_id'] does not exist within the table,
            #  update instead, or what else
            insertQuery = f"INSERT INTO creditmemo_history (increment_id, item_sku, id_eglem, item_cost, quantity_refunded, total_cost, order_id, shipping_address) VALUES {row_data}"
            cursor.execute(insertQuery)

            if not options["connection"]:
                connection.commit()

        except Exception as ex:
            logging.error("An exception has been thrown during the insertion into database: ", str(ex))

        finally:
            if options["close"]:
                SQLHelper.connectionClose(connection)
