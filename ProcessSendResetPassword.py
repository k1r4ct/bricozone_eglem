import requests
import json
from decouple import config
import logging
import datetime
from lib.helper.MagentoHelper import MagentoHelper

logging.debug(f"Start Process for sending the reset password email. Mode Exection:{config('RESET_PASSWORD_NOTIFY_MODE_EXECUTION')}. Timestamp: {datetime.datetime.now()}")

# a flag which indicate wether to populate customers' table(s) or to launch the procedure to send the
# email for resetting the password
"""
populateCustomers = True

if populateCustomers:
    MagentoHelper.populateCustomersCSV(config('INPUT_CSV_CUSTOMERS'), config('OUTPUT_CSV_CUSTOMERS'))
else:
"""
customersEmailList = []
customers = MagentoHelper.getCustomers()
# append the customers' emails to the list
for customer in customers.get('items'):
    customersEmailList.append(customer.get('email'))
# execute the request call to send the password reset email to all customers with an active email
responseList = MagentoHelper.sendResetPasswordEmail(customersEmailList)


