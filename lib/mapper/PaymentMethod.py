from enum import Enum

class PaymentMethod(Enum):

    #AZIONI_STATO_ORDINE_RICEVUTO = (['fattura', 'rimborso'], 'pending')
    NA = (None, None, None, None)
    PAYPAL = (1, 'paypal', None, 'Pagamento ricevuto') # TODO: populate the missing magento matching values 
    SCALAPAY = (2, 'scalapay', None, 'Pagamento ricevuto')
    BONIFICO = (3, 'bonifico', None, 'Pagamento ricevuto')
    CONTRASSEGNO = (4,'contrassegno', 'cashondelivery', 'Alla consegna')
    MYBANK = (5, 'mybank', 'banktransfer', 'Pagamento ricevuto')

    @classmethod
    def listMagento(cls):
        return list(map(lambda c: c.forMagento(), filter(lambda c: c.forMagento(), cls)))
    
    def getId(self):
        return self.value[0]
    
    def forEglem(self):
        return self.value[1]
    
    def forMagento(self):
        return self.value[2]
    
    def getStatus(self):
        return self.value[3]

    @classmethod
    def listEglem(cls):
        return list(map(lambda c: c.forEglem(), filter(lambda c: c.forEglem(), cls)))
    
    @classmethod
    def getPayment(cls, magentoValue):
        valueList = list(map(lambda c: c, filter(lambda c: c.forMagento() == magentoValue, cls)))
        return valueList[0] if len(valueList) else PaymentMethod.NA

    @classmethod
    def getEglemValue(cls, magentoValue):
        value = PaymentMethod.getPayment(magentoValue)
        return value.forEglem() if value else PaymentMethod.NA

    @classmethod
    def getEglemValueId(cls, magentoValue):
        value = PaymentMethod.getPayment(magentoValue)
        return value.getId() if value else None