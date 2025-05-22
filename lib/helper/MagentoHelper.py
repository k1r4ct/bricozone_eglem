# This helper implements the methods used to get the products with id_eglem from Magento,
# then to update them on the basis of the information retrieved from Eglem
import requests
import json
from  decouple import config
import logging
from datetime import datetime, timedelta
import json
from lib.helper.SQLHelper import SQLHelper
import csv
import pandas as pd

class MagentoHelper(SQLHelper):

    @staticmethod
    def getConnection():
        return SQLHelper.getConnection(config('MAGENTO_DB_HOST'), config('MAGENTO_DB_PORT', cast=int), config('MAGENTO_DB_DATABASE'), config('MAGENTO_DB_USER'), config('MAGENTO_DB_PASSWORD'))

    @staticmethod
    def connectionClose(connection):
        return SQLHelper.connectionClose(connection)

    @staticmethod
    def _getHost():
        return config('MAGENTO_HOST')

    @staticmethod
    def _getToken(options={"externalToken":False,"accessToken":None}):
        if options.get("externalToken"):
            return options.get("accessToken")
        else:
            return config('MAGENTO_TOKEN')

    @staticmethod
    def _getHeaders(options={"externalToken":False,"accessToken":None}):
        return  {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MagentoHelper._getToken(options)}"
        }

    @staticmethod
    def _call(method, urlPath, data=None, options={"externalToken":False,"accessToken":None}):
        return  requests.request(
            method.upper(),
            f"{MagentoHelper._getHost()}{urlPath}",
            headers=MagentoHelper._getHeaders(options),
            params=data if method.lower() == 'get' else None,
            json=data if method.lower() != 'get' else None,
        )

    # retrieve all the products with an id_eglem associated to, which are visible in
    # catalog and search(visibility=4) and that are active (status=1)
    def getEglemProducts(currentPage, options={"externalToken":False,"accessToken":None}):
        data = {}
        tot_count = 0
        try:
            response = MagentoHelper._call(
                "GET",
                f"/rest/all/V1/products?searchCriteria[filter_groups][0][filters][0][field]=id_eglem&searchCriteria[filter_groups][0][filters][0][value]=null&searchCriteria[filter_groups][0][filters][0][condition_type]=neq&searchCriteria[filter_groups][1][filters][0][field]=status&searchCriteria[filter_groups][1][filters][0][value]=1&searchCriteria[filter_groups][2][filters][0][field]=type_id&searchCriteria[filter_groups][2][filters][0][value]=simple&searchCriteria[filter_groups][2][filters][0][condition_type]=eq&searchCriteria[pageSize]={config('MAGENTO_GET_PRODUCTS_PAGINATION')}&searchCriteria[currentPage]={currentPage}",
                None,
                options
            )
            if response.status_code == 200:
                data = response.json()
                tot_count = data["total_count"]
        except Exception as ex:
            logging.error("An exception has been thrown during the getting of some product: ", str(ex))

        finally:
            if data != {}:
                return data["items"], tot_count
            else:
                return data, tot_count

    # This rule updates the quantity and price in one single call
    def setPriceProduct(skuProduct, price, options={"externalToken":False,"accessToken":None}):
        updateStatus = ""
        try:
            response = MagentoHelper._call(
                "PUT",
                f"/rest/all/V1/products/{skuProduct}",
                {
                    "product": {
                        "price": price
                    }
                },
                options
            )

            if response.status_code == 200:
                updateStatus = 'c'
            else:
                updateStatus = 'e'
                logging.error(f"Failed to update product {skuProduct}. Status Code: {response.status_code}, Response: {response.text}")

        except Exception as ex:
            logging.error(f"An exception has been thrown while updating Magento products: {str(ex)}")
            updateStatus = 'e'

        finally:
            return updateStatus

    def setStockProduct(skuProduct, quantity, options={"externalToken":False,"accessToken":None}):
        updateStatus = ""
        try:
            response = MagentoHelper._call(
                "POST",
                f"/rest/V1/inventory/source-items",
                {
                    "sourceItems": [
                        {
                            "sku": skuProduct,
                            "source_code": config("SOURCE_CODE_WHEREHOUSE"),
                            "quantity": quantity,
                            "status": 0 if quantity == 0 else 1
                        }
                    ]
                },
                options
            )

            if response.status_code == 200:
                updateStatus = 'c'
            else:
                updateStatus = 'e'
                logging.error(f"Failed to update product {skuProduct}. Status Code: {response.status_code}, Response: {response.text}")

        except Exception as ex:
            logging.error(f"An exception has been thrown while updating Magento products: {str(ex)}")
            updateStatus = 'e'

        finally:
            return updateStatus

    def setStockProductDatabase(productToUpdateTupla, websiteCode, statusOrderForExludeQty, methodPaymentForExludeQty, options={"connection":None, "close":True}):
        try:
            connection = options["connection"] if options["connection"] else MagentoHelper.getConnection()
            cursor = connection.cursor()
            status = statusOrderForExludeQty.replace(',', "','")
            methodPayment = methodPaymentForExludeQty.replace(',', "','")

            query = f"""
            INSERT INTO inventory_source_item(source_code, sku, quantity, status)
                SELECT
                    issl.source_code, source_stock.sku,
                    CASE WHEN reserved.qty IS NOT NULL
                        THEN IF(source_stock.stock>reserved.qty, source_stock.stock-reserved.qty, 0)
                        ELSE source_stock.stock
                    END as stock,
                    IF(IF(reserved.qty, source_stock.stock-reserved.qty, source_stock.stock)>0, 1, 0) AS status
                FROM inventory_stock_sales_channel issc
                INNER JOIN inventory_source_stock_link issl ON issl.stock_id = issc.stock_id AND issc.type = 'website' AND issc.code = %s,
                (SELECT *
                FROM (SELECT NULL AS sku, NULL AS stock) tmp
                WHERE tmp.sku IS NOT NULL
                UNION VALUES {productToUpdateTupla}) source_stock
                LEFT JOIN (
                    SELECT cpe.entity_id, cpe.sku, SUM(soi.qty_ordered) as qty
                    FROM sales_order so
                    INNER JOIN store s ON s.store_id = so.store_id
                    INNER JOIN store_website sw ON sw.website_id = s.website_id AND sw.code = %s
                    INNER JOIN sales_order_item soi ON so.entity_id = soi.order_id
                    INNER JOIN catalog_product_entity cpe ON cpe.entity_id = soi.product_id
                    INNER JOIN sales_order_payment sop ON sop.parent_id = so.entity_id
                    WHERE
                        so.status IN ('{status}')
                        AND sop.`method` IN ('{methodPayment}')
                    GROUP BY cpe.entity_id, cpe.sku
                ) reserved ON reserved.sku = source_stock.sku
            ON DUPLICATE KEY UPDATE
                    quantity=VALUES(quantity),
                    status=VALUES(status)
            """
            cursor.execute(query, (websiteCode, websiteCode))
            connection.commit()

        except Exception as ex:
            raise Exception(f"Error on update stock: {str(ex)}")

        finally:
            if options["close"]:
                MagentoHelper.connectionClose(connection)
            return

    def setPriceProductDatabase(productToUpdateTupla, websiteCode, websiteCodeGlobal, options={"connection":None, "close":True}):
        try:
            connection = options["connection"] if options["connection"] else MagentoHelper.getConnection()
            cursor = connection.cursor()
            query = f"""
                INSERT INTO catalog_product_entity_decimal(attribute_id, store_id, entity_id, value)
                    SELECT attr.attribute_id, global_store.store_id, cpe.entity_id, price.value
                    FROM (
                        SELECT *
                        FROM (SELECT NULL AS sku, NULL AS value) tmp
                        WHERE tmp.sku IS NOT NULL
                        UNION VALUES {productToUpdateTupla}
                    ) price
                    INNER JOIN catalog_product_entity cpe ON cpe.sku = price.sku
                    INNER JOIN catalog_product_website cpw ON cpe.entity_id = cpw.product_id
                    INNER JOIN store_website sw ON sw.website_id = cpw.website_id AND sw.code = %s
                    INNER JOIN store s ON s.website_id = cpw.website_id,
                    (
                        select s.store_id
                        FROM store_website sw
                        INNER JOIN store s ON s.website_id = sw.website_id AND sw.code = %s
                    ) global_store,
                    (SELECT ea.attribute_id, ea.attribute_code, ea.backend_type
                            FROM eav_attribute ea
                            LEFT JOIN eav_entity_type eet ON eet.entity_type_id = ea.entity_type_id
                            WHERE ea.attribute_code = 'price') attr
                    ON DUPLICATE KEY UPDATE value=VALUES(value)
            """
            cursor.execute(query, (websiteCode, websiteCodeGlobal))
            connection.commit()

        except Exception as ex:
            raise Exception(f"Error on update stock: {str(ex)}")

        finally:
            if options["close"]:
                MagentoHelper.connectionClose(connection)
            return

    # This rule bulk updates the quantity and price of a list of products
    def setPriceProductBulk(itemList, options={"externalToken":False,"accessToken":None}):
        data = {}
        updateStatus = ""
        try:
            itemIdEglem = None # dummy variable, only used to update product_history db table
            itemSku = None
            itemPrice = None
            dataList = []

            for item in itemList:
                itemIdEglem = item["id_eglem"] # dummy variable, only used to update product_history db table
                itemSku = item["sku"]
                itemPrice = item["price"]

                dataList.append({
                    "product": {
                        "sku": itemSku,
                        "price": itemPrice
                    }
                })

            response = MagentoHelper._call(
                "PUT",
                "/rest/all/async/bulk/V1/products",
                dataList,
                options
            )

            # the response return the uuid associated to the Cron's job that processes the queue
            data = response.json()
        except Exception as ex:
            logging.error("An exception has been thrown during a bulk update of some Magento products", str(ex))

        finally:
            if data:
                updateStatus = 'p'
                return data["bulk_uuid"], updateStatus
            else:
                raise Exception

    def setStockProductBulk(itemList, options={"externalToken":False,"accessToken":None}):
        data = {}
        updateStatus = ""
        try:
            itemSku = None
            itemQty = None
            dataList = []

            for item in itemList:
                itemSku = item["sku"]
                itemQty = item["quantity"]

                dataList.append({
                    "sourceItems": [
                        {
                            "sku": itemSku,
                            "source_code": config("SOURCE_CODE_WHEREHOUSE"),
                            "quantity": itemQty,
                            "status": 0 if itemQty == 0 else 1
                        }
                    ]
                })

            response = MagentoHelper._call(
                "POST",
                "/rest/async/bulk/V1/inventory/source-items",
                dataList,
                options
            )

            # the response return the uuid associated to the Cron's job that processes the queue
            data = response.json()
        except Exception as ex:
            logging.error("An exception has been thrown during a bulk update of some Magento products", str(ex))

        finally:
            if data:
                updateStatus = 'p'
                return data["bulk_uuid"], updateStatus
            else:
                raise Exception

    # a method to request the status code of a bulk operation on products
    def getBulkOpStatusCode(theUuid, options={"externalToken":False,"accessToken":None}):
        updateStatusList = []
        try:

            response = MagentoHelper._call(
                "GET",
                f"/rest/all/V1/bulk/{theUuid}/detailed-status",
                None,
                options
            )

            data = response.json()
            for operation in data["operations_list"]:
                if operation["serialized_data"] is None:
                    item = json.loads(operation["result_serialized_data"])
                    sku = item["sku"]
                else:
                    item = json.loads(operation["serialized_data"])
                    meta=json.loads(item["meta_information"])
                    product=meta["product"]
                    sku = product['sku']

                if operation["status"]==1:
                    updateStatusList.append({"bulk_uuid":operation["bulk_uuid"], "sku":sku, "status":'c'})
                elif operation["status"]!=4:
                    updateStatusList.append({"bulk_uuid":operation["bulk_uuid"],"sku":sku, "status":'e'})

        except Exception as ex:
            logging.error("An exception has been thrown during the request of a Magento bulk job status: ", str(ex))

        finally:
            return updateStatusList

    # retrieves the orders which have been set to a status, included inside a list
    def getOrdersByStatus(statusList, orderDelayMinute, website=None, options={"connection":None, "close":True}):
        try:
            connection = options["connection"] if options["connection"] else MagentoHelper.getConnection()
            cursor = connection.cursor()
            conditionString = ""
            status = statusList.replace(',', "','")
            if website:
                conditionString = f" AND bvsog.website_code = '{website}'"

            selectOrdersQuery = f"SELECT bvsog.* FROM {config('MAGENTO_DB_DATABASE')}.be_vw_sales_order_grouped AS bvsog WHERE bvsog.status IN ('{status}') AND bvsog.created_at <= NOW() - INTERVAL {orderDelayMinute} MINUTE {conditionString}"
            cursor.execute(selectOrdersQuery)
            queryResult = cursor.fetchall()

        except Exception as ex:
            raise Exception(f"Error on update valutazioni: {str(ex)}")

        finally:
            if options["close"]:
                MagentoHelper.connectionClose(connection)
            return queryResult


    @staticmethod
    def changeOrderStatus(order_id, order_status, options={"externalToken":False,"accessToken":None}):
        response = {}
        try:
            response = MagentoHelper._call(
                "POST",
                "/rest/V1/orders",
                {
                    "entity": {
                        "entity_id": order_id,
                        "state": order_status,
                        "status": order_status
                    }
                },
                options
            )

            if response.status_code == 200:
                response.success = True
                response.error = ''
            else:
                logging.error(f"Failed to update order {order_id}. Status Code: {response.status_code}, Response: {response.text}")
                response.success = False
                response.error = json.loads(response.text)['message']

        except Exception as ex:
            logging.error(f"An exception has been thrown while updating Magento products: {str(ex)}")
            response.success = False
            response.error = str(ex)

        return response

    @staticmethod
    def getOrder(orderId, options={"externalToken":False,"accessToken":None}):
        hasResponse = False
        try:
            response = MagentoHelper._call("GET", f"/rest/V1/orders/{orderId}", None, options)
            hasResponse = bool(response.status_code == 200)
        except Exception as ex:
            logging.error(f"Exception: {str(ex)}")

        return response.json() if hasResponse else None

    @staticmethod
    def createShipment(orderId, notify, options={"externalToken":False,"accessToken":None}):
        errorMessage = None
        try:
            order = MagentoHelper.getOrder(orderId)

            orderItems = []
            for item in order.get("items",[]):
                if item.get("product_type") == 'simple':
                    orderItems.append({
                        "order_item_id": item.get("item_id"),
                        "qty": item.get("qty_ordered")
                    })
            response = MagentoHelper._call("POST", f"/rest/V1/order/{orderId}/ship", {
                "products":orderItems,
                "notify": notify
            }, options)
            errorMessage = response.text if bool(response.status_code != 200) else None

        except Exception as ex:
            errorMessage = str(ex)
            logging.error(f"Exception: {str(ex)}")

        if errorMessage:
            raise Exception(errorMessage)
        else:
            return response.json()

    @staticmethod
    def getShipmentsByOrderId(orderId, options={"externalToken":False,"accessToken":None}):
        hasResponse = False
        try:
            response = MagentoHelper._call(
                "GET",
                f"/rest/V1/shipments?searchCriteria[filterGroups][0][filters][0][field]=order_id&searchCriteria[filterGroups][0][filters][0][value]={orderId}",
                None,
                options
            )
            hasResponse = bool(response.status_code == 200)
        except Exception as ex:
            logging.error(f"Exception: {str(ex)}")

        return response.json() if hasResponse else None

    @staticmethod
    def addTracking(orderId, trackNumber, options={"externalToken":False,"accessToken":None}):
        errorMessage = None
        tracking = {}
        try:
            shipments = MagentoHelper.getShipmentsByOrderId(orderId)

            for shipment in shipments.get("items",[]):
                if not shipment.get("track"):
                    tracking = {
                        "carrier_code": "Tracking",
                        "title": f"https://www.lamiaspedizione.it/{trackNumber}",
                        "order_id": orderId,
                        "parent_id": shipment.get("items")[0].get("parent_id"),
                        "track_number": trackNumber
                    }
                break
            response = MagentoHelper._call("POST", f"/rest/V1/shipment/track/", {"entity":tracking}, options)
            errorMessage = response.text if bool(response.status_code != 200) else None

        except Exception as ex:
            errorMessage = str(ex)
            logging.error(f"Exception: {str(ex)}")

        if errorMessage:
            raise Exception(errorMessage)
        else:
            return response.json()

    @staticmethod
    def createInvoice(orderId, options={"externalToken":False,"accessToken":None}):
        errorMessage = None

        try:
            response = MagentoHelper._call("POST", f"/rest/V1/order/{orderId}/invoice/", {"capture": False, "notify": False}, options)
            errorMessage = response.text if bool(response.status_code != 200) else None

        except Exception as ex:
            errorMessage = str(ex)
            logging.error(f"Exception: {str(ex)}")

        if errorMessage:
            raise Exception(errorMessage)
        else:
            return response.json()

    # update the orders with pending status, to pass to processing status
    def setOrderStatusBulk(orderList, options={"externalToken":False,"accessToken":None}):
        data = {}
        updateStatus = ""
        try:
            order_entity_id = None
            order_increment_id = None
            dataList = []

            for order in orderList:
                order_entity_id = order["entity_id"]
                order_increment_id = order["increment_id"]

                dataList.append({
                    "entity": {
                        "entity_id": order_entity_id,
                        "increment_id": order_increment_id,
                        "status": "processing"
                    }
                })

            response = MagentoHelper._call(
                "PUT",
                "/rest/all/async/bulk/V1/orders/create",
                dataList,
                options
            )

            # the response return the uuid associated to the Cron's job that processes the queue
            data = response.json()
        except Exception as ex:
            print("An exception has been thrown during a bulk update of some Magento orders' status", str(ex))

        finally:
            if data:
                updateStatus = 'p'
                return data["bulk_uuid"], updateStatus
            else:
                return data, updateStatus

    # a method to request the status code of a bulk operation on orders
    def getBulkOpStatusCodeOrders(theUuid, options={"externalToken":False,"accessToken":None}):
        updateStatusList = []
        try:
            response = MagentoHelper._call(
                "GET",
                f"/rest/all/V1/bulk/{theUuid}/detailed-status",
                None,
                options
            )
            data = response.json()

            for operation in data["operations_list"]:
                if operation["serialized_data"] is None:
                    item = json.loads(operation["result_serialized_data"])
                    increment_id = item["increment_id"]
                else:
                    item = json.loads(operation["serialized_data"])
                    meta=json.loads(item["meta_information"])
                    entity=meta["entity"]
                    increment_id = entity["increment_id"]

                if operation["status"]==1:
                    updateStatusList.append({"bulk_uuid":operation["bulk_uuid"], "increment_id":increment_id, "status":'c'})
                elif operation["status"]!=4:
                    updateStatusList.append({"bulk_uuid":operation["bulk_uuid"],"increment_id":increment_id, "status":'e'})

        except Exception as ex:
            print("An exception has been thrown during the request of a Magento bulk job status: ", str(ex))

        finally:
            return updateStatusList

    # a method to get the credit memos
    # TODO: check if it is necessary to insert shop code inside the request url (value default by default, all for all or specific values)
    # TODO 2: check the returned fields of a call towards a credit memo in which only part of the order items has been refunded
    def getCreditMemos(currentPage, options={"externalToken":False,"accessToken":None}):
        data = {}
        tot_count = 0
        try:
            response = MagentoHelper._call(
                "GET",
                f"/rest/V1/creditmemos?searchCriteria[filter_groups][0][filters][0][field]=created_at&searchCriteria[filter_groups][0][filters][0][value]=1900-01-01&searchCriteria[filter_groups][0][filters][0][condition_type]=gteq&searchCriteria[pageSize]={config('MAGENTO_GET_CREDITMEMOS_PAGINATION')}&searchCriteria[currentPage]={currentPage}",
                None,
                options
            )
            if response.status_code == 200:
                data = response.json()
                tot_count = data["total_count"]
        except Exception as ex:
            print("An exception has been thrown during the request of products with id_eglem from Magento: ", str(ex))

        finally:
            if data != {}:
                return data["items"], tot_count
            else:
                return data, tot_count

    # a method to get the details of a specific product
    def getProductDetails(productSku, options={"externalToken":False,"accessToken":None}):
        data = {}
        try:
            response = MagentoHelper._call(
                "GET",
                f"/rest/V1/products/{productSku}",
                None,
                options
            )
            if response.status_code == 200:
                data = response.json()
        except Exception as ex:
            print("An exception has been thrown during the request of products with id_eglem from Magento: ", str(ex))

        finally:
            return data

    @staticmethod
    def procedureUpdateBestsellers(bestsellersWebsite, bestsellersDay, bestsellersProduct, options={"connection":None, "close":True}):
        try:
            connection = options["connection"] if options["connection"] else MagentoHelper.getConnection()
            cursor = connection.cursor()
            procedureBestsellers = f"CALL {config('MAGENTO_DB_DATABASE')}.be_pr_update_bestsellers('{bestsellersWebsite}', {bestsellersDay}, {bestsellersProduct})"
            cursor.execute(procedureBestsellers)
            connection.commit()

        except Exception as ex:
            raise Exception(f"Error on update bestsellers: {str(ex)}")

        finally:
            if options["close"]:
                MagentoHelper.connectionClose(connection)

    @staticmethod
    def procedureUpdateValutazioni(valutazioniWebsite, valutazioniDay, options={"connection":None, "close":True}):
        try:
            connection = options["connection"] if options["connection"] else MagentoHelper.getConnection()
            cursor = connection.cursor()
            procedureValutazioni = f"CALL {config('MAGENTO_DB_DATABASE')}.be_pr_update_valutazioni('{valutazioniWebsite}', {valutazioniDay})"
            cursor.execute(procedureValutazioni)
            connection.commit()

        except Exception as ex:
            raise Exception(f"Error on update valutazioni: {str(ex)}")

        finally:
            if options["close"]:
                MagentoHelper.connectionClose(connection)

    @staticmethod
    def getQuantityProduct(sku, options={"connection":None, "close":True}):
        try:
            connection = options["connection"] if options["connection"] else MagentoHelper.getConnection()
            cursor = connection.cursor()
            query = f"""
                SELECT
                    isi.quantity
                FROM
                    {config('MAGENTO_DB_DATABASE')}.catalog_product_entity cpe
                INNER JOIN inventory_source_item isi
                    ON cpe.sku = isi.sku and isi.source_code = 'CS'
                WHERE
                    cpe.type_id = 'simple'
                    AND cpe.sku = %s
            """
            cursor.execute(query, (sku))
            queryResult = cursor.fetch()

        except Exception as ex:
            raise Exception(f"Error on get quantity: {str(ex)}")

        finally:
            if options["close"]:
                MagentoHelper.connectionClose(connection)
            return queryResult
        
    # get the magento customers with an active email
    @staticmethod
    def getCustomers(options={"externalToken":False,"accessToken":None}):
        data = {}
        try:
            response = MagentoHelper._call(
                "GET",
                f"/rest/V1/customers/search?searchCriteria[filter_groups][0][filters][0][field]=email&searchCriteria[filter_groups][0][filters][0][value]=rosario.roccella@bcame.it&searchCriteria[filter_groups][0][filters][0][condition_type]=eq",
                None,
                options
            )
            if response.status_code == 200:
                data = response.json()
        except Exception as ex:
            print("An exception has been thrown during the request of customers with an active email from Magento: ", str(ex))

        finally:
            return data
        
    # TODO: Before launching the following procedure it is necessary to set the "Forgot Email Template"
    # to "brico-reset-password-after-migration". This section is located within backoffice, 
    # inside the section Stores->Configuration->Customer Configuration->Password Options, after
    # have launched the procedure it is possible to set the template as the one previously used
    # This method sends a reset password email to magento customers
    def sendResetPasswordEmail(customerEmailList, options={"externalToken":False,"accessToken":None}):
        try:
            responseList = []
            for customerEmail in customerEmailList:
                response = MagentoHelper._call(
                    "PUT",
                    f"/rest/all/V1/customers/password",
                    {
                        "email": customerEmail,
                        "template": "email_reset",
                        "websiteId": 2
                        
                    },
                    options
                )

            if response.status_code != 200:
                logging.error(f"Failed to send the reset password email to {customerEmail}. Status Code: {response.status_code}, Response: {response.text}")

            responseList.append(response)

        except Exception as ex:
            logging.error(f"An exception has been thrown while updating Magento products: {str(ex)}")

        finally:
            return responseList
        
    # @staticmethod    
    # def populateCustomersCSV(inputCSV, outputCSV):
    #     # read specific columns of csv file using Pandas
    #     df = pd.read_csv(inputCSV, usecols=['email', 'firstname', 'lastname'])

    #     # the header of the output csv
    #     header = ['email', '_website', '_store', 'created_in', 'firstname', 'group_id', 'lastname']
        
    #     with open(outputCSV, 'w', newline='') as csvfile:
    #         csvWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    #         csvWriter.writerow(header)

    #         for index, customer in df.iterrows():
    #             csvWriter.writerow([customer['email'],
    #                             'bricozone', 
    #                             'bz_it', 
    #                             'Bricozone Italia', 
    #                             customer['firstname'],
    #                             1,
    #                             customer['lastname']])
                

    @staticmethod
    def getCustomAttributeValue(attribute, customAttributeList):
        customAttribute = list(filter(lambda x: x.get("attribute_code") == attribute, customAttributeList))
        return customAttribute[0].get("value") if len(customAttribute) else None

