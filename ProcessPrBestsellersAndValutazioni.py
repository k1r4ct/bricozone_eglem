
from lib.helper.MagentoHelper import MagentoHelper
from decouple import config
import datetime
import logging

# Initialize Logger
logging.basicConfig(filename=config('LOGGING_FILE'), level=config('LOGGING_LEVEL'))

try:
    if config("PR_UPDATE_MODE_EXECUTION") == 'bestsellers':
        MagentoHelper.procedureUpdateBestsellers(config('PR_UPDATE_BESTSELLERS_WEBSITE_CODE'), config('PR_UPDATE_BESTSELLERS_EVALUATION_DAY'), config('PR_UPDATE_BESTSELLERS_EVALUATION_PRODUCT'))
    elif config("PR_UPDATE_MODE_EXECUTION") == 'valutazioni':
        MagentoHelper.procedureUpdateValutazioni(config('PR_UPDATE_VALUTAZIONI_WEBSITE_CODE'), config('PR_UPDATE_VALUTAZIONI_EVALUATION_DAY'))
        logging.debug(f"Procedure for update valutazioni is completed. Timestamp: {datetime.datetime.now()}")
    elif config("PR_UPDATE_MODE_EXECUTION") == 'all':
        MagentoHelper.procedureUpdateBestsellers(config('PR_UPDATE_BESTSELLERS_WEBSITE_CODE'), config('PR_UPDATE_BESTSELLERS_EVALUATION_DAY'), config('PR_UPDATE_BESTSELLERS_EVALUATION_PRODUCT'))
        MagentoHelper.procedureUpdateValutazioni(config('PR_UPDATE_VALUTAZIONI_WEBSITE_CODE'), config('PR_UPDATE_VALUTAZIONI_EVALUATION_DAY'))
        logging.debug(f"Procedure for update bestsellers and valutazioni are completed. Timestamp: {datetime.datetime.now()}")
    else:
        exit(1)
except Exception as e:
    logging.error(f"{e}. Timestamp: {datetime.datetime.now()}")