# A simple Main method to update the products' price and stock quantity
from lib.helper.MagentoHelper import MagentoHelper
from lib.helper.EglemHelper import EglemHelper
from lib.helper.BorderDbHelper import BorderDbHelper
from decouple import config
import math
import logging
import datetime

itemListPrice, itemListQuantity = [], []
hasNextPage, currentPage = True, 1
connectionBorder = BorderDbHelper.getConnection()
pagination_limit = config('MAGENTO_GET_PRODUCTS_PAGINATION', cast=int)

tuplePriceList = []
tupleQuantityList = []
itemPriceList = []
itemQuantityList = []

logging.debug(f"Start Process for update stock and price. Mode Exection:{config('UPDATE_STOCK_AND_PRICE_MODE_EXECUTION')}. Timestamp: {datetime.datetime.now()}")
try:
    while hasNextPage:
        magentoProducts, totalCount = MagentoHelper.getEglemProducts(currentPage)
        productMap = {
            [attr["value"] for attr in product["custom_attributes"] if attr["attribute_code"] == 'id_eglem'][0]: product
            for product in magentoProducts
        }
        productIds = list(productMap.keys())
        eglemProducts = EglemHelper.getProducts(productIds)

        for eglemProduct in eglemProducts:
            idEg = eglemProduct['id']
            magentoProduct = productMap[idEg]
            sku = magentoProduct["sku"]
            price, quantity = eglemProduct["prezzo"], int(eglemProduct["quantita"])
            priceMagento = magentoProduct["price"]

            if config('UPDATE_STOCK_AND_PRICE_MODE_EXECUTION') == 'database':
                tuplePriceList.append(f"('{sku}' , {price})")
                itemListPrice.append({"sku": sku, "id_eglem": idEg, "price": price, "quantity": None})
                tupleQuantityList.append(f"('{sku}' , {quantity})")
                itemListQuantity.append({"sku": sku, "id_eglem": idEg, "price": None, "quantity": quantity})
                continue
            elif config('UPDATE_STOCK_AND_PRICE_MODE_EXECUTION') == 'bulk':
                if price != priceMagento:
                    itemListPrice.append({"sku": sku, "id_eglem": idEg, "price": price, "quantity": None})
                    BorderDbHelper.insertProductHistory(sku, idEg, None, quantity, updateStatusQuantity, None, {"connection": connectionBorder, "close": False})
                itemListQuantity.append({"sku": sku, "id_eglem": idEg, "price": None, "quantity": quantity})
                continue
            elif config('UPDATE_STOCK_AND_PRICE_MODE_EXECUTION') == 'api':
                if price != priceMagento:
                    updateStatusPrice = MagentoHelper.setPriceProduct(sku, price)
                    BorderDbHelper.insertProductHistory(sku, idEg, price, None, updateStatusPrice, None, {"connection": connectionBorder, "close": False})
                updateStatusQuantity = MagentoHelper.setStockProduct(sku, quantity)

        hasNextPage = pagination_limit > 0 and currentPage < math.ceil(totalCount / pagination_limit)
        currentPage += 1 if hasNextPage else 0

    if config('UPDATE_STOCK_AND_PRICE_MODE_EXECUTION') == 'database':
        if tuplePriceList or tupleQuantityList:
            connectionMagento = MagentoHelper.getConnection()
            # INSERT PRICE
            MagentoHelper.setPriceProductDatabase(",".join(tuplePriceList), config("UPDATE_PRICE_WEBSITE_CODE"), config('UPDATE_PRICE_GLOBAL_WEBSITE_CODE'), {"connection": connectionMagento, "close": False})
            BorderDbHelper.insertProductsHistory(itemListPrice, 'c', None, {"connection": connectionBorder, "close": False})
            logging.info(f"Update Price complete. Timestamp: {datetime.datetime.now()}")
            # INSERT QUANTITY
            MagentoHelper.setStockProductDatabase(",".join(tupleQuantityList), config("UPDATE_STOCK_WEBSITE_CODE"),  config("STATUS_ORDER_FOR_EXCLUDE_QUANTITY"),  config("METHOD_PAYMENT_FOR_EXCLUDE_QUANTITY"), {"connection": connectionMagento, "close": True})
            BorderDbHelper.insertProductsHistory(itemListQuantity, 'c', None, {"connection": connectionBorder, "close": False})
            logging.info(f"Update Stock complete. Timestamp: {datetime.datetime.now()}")
    elif config('UPDATE_STOCK_AND_PRICE_MODE_EXECUTION') == 'bulk':
        if itemListPrice:
            jobUuidPrice, updateStatusPrice = MagentoHelper.setPriceProductBulk(itemListPrice)
            BorderDbHelper.insertProductsHistory(itemListPrice, updateStatusPrice, jobUuidPrice, {"connection": connectionBorder, "close": False})
        if itemListQuantity:
            jobUuidQuantity, updateStatusQuantity = MagentoHelper.setStockProductBulk(itemListQuantity)
            BorderDbHelper.insertProductsHistory(itemListQuantity, updateStatusQuantity, jobUuidQuantity, {"connection": connectionBorder, "close": False})
except Exception as ex:
    logging.error("An exception has been thrown during the insertion into database: ", str(ex))
finally:
    BorderDbHelper.connectionClose(connectionBorder)
    logging.debug(f"Finish Process. Timestamp: {datetime.datetime.now()}")