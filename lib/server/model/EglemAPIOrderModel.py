# Define the data models
from pydantic import BaseModel, Field
from typing import Optional, List

class LineItem(BaseModel):
    id_prodotto: int
    id_prodotto_eglem: int
    quantita: int
    prezzo_lineitem: float


class Pagamento(BaseModel):
    id: int
    id_metodo_pagamento: int
    metodo_pagamento: str
    data_ricezione_pagamento: Optional[str]
    id_ordine: str
    importo_dovuto: str
    importo_pagato: Optional[str]
    status: str
    json_data: Optional[str]
    token: Optional[str]

    # mapping methods
    @staticmethod
    def getMappedPaymentValues(keyToMap):
        payment_method = {"cashondelivery": "contrassegno", "banktransfer": "mybank" }
        #payment_method = {"poscash": "contrassegno", "poscreditcard": "mybank", "checkmo": "mybank", "adyen_pay_by_link": "mybank" }  # TODO: il mapping è utile solo perchè la get sugli ordini viene effettuata su magento, su eglem i campi sono diversi
        return payment_method[keyToMap]

    @staticmethod
    def getIdMappedPaymentValues(keyToMap):
        id_payment_method = {"paypal": 1, "scalapay": 3, "bonifico": 4, "contrassegno": 5, "mybank": 6}
        return id_payment_method[keyToMap]

    @staticmethod
    def getMappedPaymentStatus(keyToMap):
        paymentStatus = {"paypal": "Pagamento ricevuto", "scalapay": "Pagamento ricevuto", \
                          "bonifico": "Pagamento ricevuto", "contrassegno": "Alla consegna", "mybank": "Pagamento ricevuto"}
        return paymentStatus[keyToMap]

class Order(BaseModel):
    id: int
    id_timestamp: str
    created_at: str
    id_utente: int
    lineitems: List[LineItem]
    destinatario_s: str
    indirizzo_s: str
    comune_s: str
    cap_s: str
    provincia_s: str
    nazione_s: str
    telefono_s: str
    pagamento: Pagamento
    id_metodo_pagamento: int
    metodo_pagamento: str
    stato_pagamento: str
    id_pagamento: int
    servizi_extra: Optional[str]
    servizi_extra_dettagli: Optional[List[str]]
    totale_prodotti: int
    totale_trasporto: float
    totale_servizi_extra: int
    commissioni_metodo_pagamento: float
    commissioni: float
    totale_ordine: float
    note: Optional[str]
    metodo_spedizione: Optional[str]
    codice_tracking: Optional[str]
    stato_ordine: str
    azioni_disponibili: List[str]
    email: str
    cellulare: str
    data_ordine: str

    # mapping methods TODO: check bricozone status "Spedito"
    def getMappedOrderStatus(keyToMap):
        orderStatus = {"pending": "Ricevuto", "Processing": "In lavorazione", "Complete": "Consegnato", "Canceled": "Annullato" }
        return orderStatus[keyToMap]
    
    def getMappedStatusActions(keyToMap):
        availableActions = {"Ricevuto": ["fattura", "rimborso"]}
        return availableActions[keyToMap]

class OrderResponse(BaseModel):
    status: bool = Field(default_factory=False)
    count: int
    lista_ordini: List[Order]