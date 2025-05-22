# A simple Main method to launch a Magento API get for retrieving the status code of a bulk operation
from lib.helper.MagentoHelper import MagentoHelper
from lib.helper.EglemHelper import EglemHelper
from lib.helper.SQLHelper import SQLHelper
from decouple import config
import logging

# Initialize Logger
logging.basicConfig(filename=config('LOGGING_FILE'), level=config('LOGGING_LEVEL'))

uuidList = SQLHelper.getProductHistoryStatus('p')
# it launches a get request to the magento endpoint related to bulk operations, and
# save the list of resulting operations into a product history database table
print(uuidList)
for uuid in uuidList:
    print(uuid[0])
    updateStatusList = MagentoHelper.getBulkOpStatusCode(uuid[0])

    # update product_history table only if the status code associated to one or more products has changed, from an earlier bulk operation
    if updateStatusList:
        SQLHelper.updateProductHistoryBulk(updateStatusList)
