import requests
from decouple import config
import json
import logging

class EglemHelper:

    @staticmethod
    def _getHost():
        return config('EGLEM_HOST')
    
    @staticmethod
    def _getHeaders():
        return {
            "Authorization": f"Bearer {config('EGLEM_TOKEN')}"
        }

    # a method to get all the products from Eglem, referenced by a list
    def getProducts(idList):
        data_res = []
        try:
            payload = {
                'token': config('EGLEM_TOKEN'),
                'act': 'get_dati_da_lista_prodotti',
                'dati': '["quantita","prezzo"]',
                'list': json.dumps(idList)
            }
            response = requests.request(
                "POST", 
                EglemHelper._getHost(), 
                headers=EglemHelper._getHeaders(), 
                data=payload
            )
            if response.status_code == 200:
                data = response.json()
                data_res = data["res"]
            else:
                logging.error(f"An exception has been thrown: Status code: {response.status_code}, Response: {response.text}")
                data_res = []
        
        except Exception as ex:
            logging.error("An exception has been thrown during the retrieval of some products from Eglem: ", str(ex))

        finally:
            return data_res
        