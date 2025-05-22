# The controllers used by the server proxy
from lib.helper.MagentoHelper import MagentoHelper
#from helper.SQLHelper import SQLHelper
from lib.server.model.EglemAPIOrderModel import OrderResponse, Order, Pagamento, LineItem
from lib.server.model.ResponseHttpModel import ResponseHttp
from lib.mapper.OrderStatus import OrderStatus
from lib.mapper.PaymentMethod import PaymentMethod
from decouple import config
from fastapi import HTTPException
import traceback
from dotmap import DotMap
import json
from datetime import datetime


class OrderController:

    @staticmethod
    def getOrders():
        try:
            data = MagentoHelper.getOrdersByStatus(config('ORDER_STATUS_LIST'), config('ORDER_DELAY_MINUTES'), config('ORDER_WEBSITE', default=None))

            responseObj = DotMap({
                "status": len(data) > 0,
                "count": len(data),
                "lista_ordini": []
            }) #OrderResponse

            for inOrder in data:
                inOrder = {
                    'order_id': inOrder[0],
                    'created_at': inOrder[1].strftime("%Y-%m-%d %H:%M:%S"),
                    'items': inOrder[2],
                    'firstname': inOrder[3],
                    'lastname': inOrder[4],
                    'email': inOrder[5],
                    'city': inOrder[6],
                    'postcode': inOrder[7],
                    'region_code': inOrder[8],
                    'country_id': inOrder[9],
                    'telephone': inOrder[10],
                    'street': inOrder[11],
                    'payment_method': inOrder[12],
                    'amount_ordered': float(inOrder[13]),
                    'total_qty_ordered': float(inOrder[14]),
                    'base_shipping_incl_tax': float(inOrder[15]),
                    'status': inOrder[16],
                    'website_code': inOrder[17]
                }
                outOrder = DotMap() #Order
                outOrder.lineitems = []
                outOrder.id_timestamp = "" # default value
                outOrder.created_at = str(inOrder.get("created_at", None))
                outOrder.id_utente = 0 # default value

                outOrder.id = inOrder.get("order_id", None)

                eglemOrderPayment = DotMap() #Pagamento
                orderProducts = json.loads(inOrder.get('items'))
                for inProduct in orderProducts:
                    outProduct = DotMap() #LineItem
                    outProduct.id_prodotto = inProduct.get('id')
                    outProduct.id_prodotto_eglem = inProduct.get('id_eglem')
                    outProduct.quantita = inProduct.get("qty_ordered")
                    outProduct.prezzo_lineitem = inProduct.get("original_price")

                    # append the product to lineitems product list
                    outOrder.lineitems.append(outProduct)

                outOrder.destinatario_s = inOrder.get("firstname") + " " + inOrder.get("lastname")
                outOrder.indirizzo_s = inOrder.get("street")
                outOrder.comune_s = inOrder.get("city")
                outOrder.cap_s = inOrder.get("postcode")
                outOrder.provincia_s = inOrder.get("region_code")
                outOrder.nazione_s = inOrder.get("country_id")
                outOrder.telefono_s = inOrder.get("telephone")
                eglemOrderPayment.id = None

                #paymentMethod = inOrder.get('payment_method')
                paymentMethod = PaymentMethod.getPayment(inOrder.get('payment_method'))
                if paymentMethod:
                    eglemOrderPayment.metodo_pagamento = paymentMethod.forEglem()
                    eglemOrderPayment.id_metodo_pagamento = paymentMethod.getId()

                eglemOrderPayment.data_ricezione_pagamento = str(inOrder.get('created_at', None))
                eglemOrderPayment.id_ordine = str(inOrder.get('order_id', None))
                eglemOrderPayment.importo_dovuto = str(inOrder.get('amount_ordered'))
                # TODO: check if metodo_pagamento = "contrassegno" then importo_pagato = null, else importo_pagato = importo_dovuto
                eglemOrderPayment.importo_pagato = None if eglemOrderPayment.metodo_pagamento == PaymentMethod.CONTRASSEGNO.forEglem() else eglemOrderPayment.importo_dovuto
                # TODO: check value to associate with metodo_pagamento = mybank, and check if the status of each metodo_pagamento
                #  is the same for every transaction which owns that metodo_pagamento
                eglemOrderPayment.status = paymentMethod.getStatus()

                eglemOrderPayment.json_data = None
                eglemOrderPayment.token = None
                outOrder.pagamento = eglemOrderPayment
                outOrder.id_metodo_pagamento = eglemOrderPayment.id_metodo_pagamento
                outOrder.metodo_pagamento = eglemOrderPayment.metodo_pagamento
                outOrder.stato_pagamento = eglemOrderPayment.status
                outOrder.id_pagamento = eglemOrderPayment.id
                outOrder.servizi_extra = "" # default
                outOrder.servizi_extra_dettagli = [] # default
                outOrder.totale_prodotti = inOrder.get("total_qty_ordered", None)
                outOrder.totale_trasporto = inOrder.get("base_shipping_incl_tax", None)
                outOrder.totale_servizi_extra = 0 # default
                outOrder.commissioni_metodo_pagamento = 0 # default
                outOrder.commissioni = 0 # default
                outOrder.totale_ordine = inOrder.get('amount_ordered')
                if inOrder.get("status_histories"):
                    outOrder.note = inOrder.get("status_histories", [{"comment": None}])[0].get("comment", None)  
                    # It takes the last comment inserted, that is the first in list ["status_histories"][0]
                else:
                    outOrder.note = ""
                outOrder.metodo_spedizione = None # it is set to null for each order from eglem
                outOrder.codice_tracking = None # default

                outOrder.stato_ordine = OrderStatus.getEglemValue(inOrder.get("status")) # TODO: check missing mapping value of "Spedito"
                outOrder.azioni_disponibili = ["fattura", "rimborso"]

                # TODO: check if the email is the one set within shipment info, or the general one
                outOrder.email = inOrder.get("email", None)
                outOrder.cellulare = inOrder.get("telephone", None)
                outOrder.data_ordine = outOrder.created_at = str(inOrder.get("created_at", None))

                responseObj.lista_ordini.append(outOrder)

            return responseObj.toDict()
        except KeyError as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Missing expected key: {traceback.print_exception(e)}")
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {traceback.print_exception(e)}")

    @staticmethod
    def changeOrderStatus(orders_and_status, token):
        errors = []
        notify = False

        if not isinstance(orders_and_status, list):
            raise HTTPException(status_code=415, detail="Elenco non valido")

        for order in orders_and_status:
            if order.get('stato') not in OrderStatus.listEglem():
                errors.append({
                    'id': order.get('id'),
                    'error': f"Stato {order.get('stato')} non previsto"
                })
                continue

            if order.get('stato') == OrderStatus.IN_LAVORAZIONE.forEglem():
                status = OrderStatus.IN_LAVORAZIONE.forMagento()
            elif order.get('stato') == OrderStatus.SPEDITO.forEglem():
                status = OrderStatus.SPEDITO.forMagento()
                notify = True
                try:
                    MagentoHelper.createShipment(order.get('id'), notify, {"externalToken": True, "accessToken":token})
                except Exception as e:
                    errors.append({
                        'id': order.get('id'),
                        'error': str(e)
                    })
                    continue
            elif order.get('stato') == OrderStatus.RICEVUTO.forEglem():
                try:
                    orderMagento = MagentoHelper.getOrder(order.get('id'), {"externalToken": True, "accessToken":token})
                    if orderMagento.get("payment",{"method":None}).get("method") == PaymentMethod.CONTRASSEGNO.forMagento():
                        MagentoHelper.createInvoice(order.get('id'), {"externalToken": True, "accessToken":token})
                except Exception as e:
                    #errors.append({
                    #    'id': order.get('id'),
                    #   'error': str(e)
                    #})
                    pass
                status = OrderStatus.RICEVUTO.forMagento()
            elif order.get('stato') == OrderStatus.CONSEGNATO.forEglem():
                status = OrderStatus.CONSEGNATO.forMagento()
            elif order.get('stato') == OrderStatus.ANNULLATO.forEglem():
                status = OrderStatus.ANNULLATO.forMagento()

            responseMagento = MagentoHelper.changeOrderStatus(order.get('id'), status, {"externalToken": True, "accessToken":token})

            if not responseMagento.success:
                errors.append({
                    'id': order.get('id'),
                    'error': responseMagento.error
                })

        if len(errors) > 0:
            response = ResponseHttp(status_code = 206, content = {'message': 'Alcuni ordini non sono stati correttamente aggiornati', 'data': errors}).model_dump()
        else:
            response = ResponseHttp(status_code = 200, content = {'message': 'Tutti gli ordini sono stati correttamente aggiornati.'}).model_dump()

        return response

    @staticmethod
    def addTracking(id_ordine, codice_tracking, token):
        try:
            MagentoHelper.addTracking(id_ordine, codice_tracking, {"externalToken": True, "accessToken":token})
            response = ResponseHttp(status_code = 200, content = {'message': 'Tracking aggiornato correttamente'}).model_dump()
        except Exception as e:
            response = ResponseHttp(status_code = 400, content = {'message': str(e)}).model_dump()
        return response

    @staticmethod
    def addTrackings(data, token):
        response = {
            'ok': 0,
            'ko': 0,
            'updated' : [],
            'failed': []
        }

        if not isinstance(data, list) or not data:
            raise HTTPException(status_code=415, detail="Dati non validi")

        for order in data:
            id_ordine = order.get('id_ordine_esterno')
            try:
                if order.get('stato') == "Spedito":
                    MagentoHelper.addTracking(id_ordine, order.get('codice_tracking'), {"externalToken": True, "accessToken":token})
                elif order.get('stato') == "Consegnato":
                    MagentoHelper.changeOrderStatus(id_ordine, OrderStatus.CONSEGNATO.forMagento(), {"externalToken": True, "accessToken":token})
                response['ok'] += 1
                response['updated'].append(id_ordine)
            except Exception:
                response['ko'] += 1
                response['failed'].append(id_ordine)

        if len(data) == response.get('ok'):
            response = ResponseHttp(status_code = 200, content = {'message': f"Tutti i {response.get('ok')} tracking sono stati comunicati correttamente", 'data':response}).model_dump()
        else:
            response = ResponseHttp(status_code = 206, content = {'message': f"Su {len(data)} ordini, {response.get('ko')} tracking non sono stati comunicati correttamente: {','.join(response.get('failed'))}", 'data':response}).model_dump()

        return response

