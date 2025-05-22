# A simple Main method to instantiate the helper classes
from lib.helper.MagentoHelper import MagentoHelper
from lib.helper.EglemHelper import EglemHelper
from lib.helper.SQLHelper import SQLHelper
from decouple import config
import math
import logging
# Initialize Logger
logging.basicConfig(filename=config('LOGGING_FILE'), level=config('LOGGING_LEVEL'))

orderList = []
hasNextPage = True
currentPage = 1
updateStatus = ""  
while hasNextPage:
    magentoOrders, totalCount = MagentoHelper.getOrdersByStatus(currentPage)

    for order in magentoOrders:
        orderList.append({"entity_id": order["entity_id"], "increment_id": order["increment_id"], "status": order["status"]})
    
    hasNextPage = False if int(config('MAGENTO_GET_ORDERS_PAGINATION')) == 0 else currentPage<math.ceil(totalCount/int(config('MAGENTO_GET_ORDERS_PAGINATION')))
    if hasNextPage:
        currentPage+=1

print(orderList)

if not config("BULK_ENABLE", cast=bool):
    for order in orderList:
        response, updateStatus = MagentoHelper.setOrderStatus(order["entity_id"], order["increment_id"])
    # insert the results of the non-bulk operations into order_history table, only if updateStatus is not empty
    if updateStatus:
        SQLHelper.insertOrderHistory(orderList, updateStatus)

else:
    if orderList:
        jobUuid, updateStatus = MagentoHelper.setOrderStatusBulk(orderList)
        # insert the orders whose fields have to be updated into order_history table, with all the status set to pending, 
        # before a get request to retrieve the final status is executed, only if updateStatus is not empty
        if updateStatus:
            SQLHelper.insertOrderHistory(orderList, updateStatus, jobUuid)
        #updateStatusList = MagentoHelper.getBulkOpStatusCodeOrders(jobUuid) # move into second main

        

"""
# creditmemoList will be the list containing all the credtimemo, with all the useful information, like shipping address, and the item list
creditmemoList = []
hasNextPage = True
currentPage = 1
while hasNextPage:
    # retrieves all the creditmemos from magento, starting from a certain date
    creditmemos, totalCount = MagentoHelper.getCreditMemos(currentPage)

    #print(creditmemos[0])

    for creditmemo in creditmemos:
        # retrieves the details of the order associated to the creditmemo
        orderDetails = MagentoHelper.getOrderDetails(creditmemo["order_id"])
        # create the dictionary with the elements that make the complete address
        shipping = {"city": orderDetails["extension_attributes"]["shipping_assignments"][0]["shipping"]["address"]["city"], \
                    "country_id": orderDetails["extension_attributes"]["shipping_assignments"][0]["shipping"]["address"]["country_id"], \
                    "postcode": orderDetails["extension_attributes"]["shipping_assignments"][0]["shipping"]["address"]["postcode"], \
                    "region": orderDetails["extension_attributes"]["shipping_assignments"][0]["shipping"]["address"]["region"], \
                    "region_code": orderDetails["extension_attributes"]["shipping_assignments"][0]["shipping"]["address"]["region_code"], \
                    "street": orderDetails["extension_attributes"]["shipping_assignments"][0]["shipping"]["address"]["street"][0]}
        # TODO: Eventually for using with Eglem call, and insertion into border database
        phone_number = orderDetails["extension_attributes"]["shipping_assignments"][0]["shipping"]["address"]["telephone"]
        email = orderDetails["extension_attributes"]["shipping_assignments"][0]["shipping"]["address"]["email"]

        
        # constructs the shipping address starting from the dictionary
        shippingAddress = shipping["city"] + ", " + shipping["country_id"] + ", " + shipping["postcode"] + ", " + shipping["region"] + \
        ", " + shipping["region_code"] + ", " + shipping["street"]

        items = []
        for item in creditmemo["items"]:
            # TODO: the entire procedure will be exectuted on creditememo with items that own an id_eglem, the following lines will be
            # modified accordingly
            print(item)
            itemDetails = MagentoHelper.getProductDetails(item["sku"])
            idEglem = [x["value"] for x in itemDetails["custom_attributes"] if x["attribute_code"] == 'id_eglem']
            if not idEglem:
                idEglem = None                                                                               # TODO: check that item["qty"] refers to item qty refunded
            items.append({"item_sku": item["sku"], "id_eglem": idEglem, "item_cost": item["price_incl_tax"], "quantity_refunded": item["qty"]})
        creditmemoList.append({"creditmemo_id": creditmemo["increment_id"], "items": items, "total_cost": creditmemo["grand_total"], "order_id": creditmemo["order_id"], "shipping_address": shippingAddress})
    print(creditmemoList[0]["items"])


    hasNextPage = False# if int(config('MAGENTO_GET_CREDITMEMOS_PAGINATION')) == 0 else currentPage<math.ceil(totalCount/int(config('MAGENTO_GET_CREDITMEMOS_PAGINATION')))
    if hasNextPage:
        currentPage+=1
for creditmemo in creditmemoList:
    SQLHelper.insertCreditmemoHistory(creditmemo)
"""
