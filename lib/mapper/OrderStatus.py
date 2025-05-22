from enum import Enum

class OrderStatus(Enum):
    IN_LAVORAZIONE = ('In lavorazione','processing')
    RICEVUTO = ('Ricevuto','taken_over_by_warehouse')
    ANNULLATO = ('Annullato','canceled')
    SPEDITO = ('Spedito' ,'complete')
    CONSEGNATO = ('Consegnato','delivered')

    def forEglem(self):
        return self.value[0]

    def forMagento(self):
        return self.value[1]

    @classmethod
    def listEglem(cls):
        return list(map(lambda c: c.forEglem(), cls))
    
    @classmethod
    def listMagento(cls):
        return list(map(lambda c: c.forMagento(), cls))
    
    @classmethod
    def getStatus(cls, magentoValue):
        valueList = list(map(lambda c: c, filter(lambda c: c.forMagento() == magentoValue, cls)))
        return valueList[0] if len(valueList) else None
    
    @classmethod
    def getEglemValue(cls, magentoValue):
        value = OrderStatus.getStatus(magentoValue)
        return value.forEglem() if value else None
    





'''
print(OrderStatus.STATO_ORDINE_IN_LAVORAZIONE.forEglem())
status = ''

match 'Annullato':
    case OrderStatus.STATO_ORDINE_IN_LAVORAZIONE.forEglem():
        status = OrderStatus.STATO_ORDINE_IN_LAVORAZIONE.forMagento()
    case OrderStatus.STATO_ORDINE_SPEDITO.forEglem():
        status = OrderStatus.STATO_ORDINE_SPEDITO.forMagento()
    case OrderStatus.STATO_ORDINE_RICEVUTO.forEglem():
        status = OrderStatus.STATO_ORDINE_RICEVUTO.forMagento()
    case OrderStatus.STATO_ORDINE_CONSEGNATO.forEglem():
        status = OrderStatus.STATO_ORDINE_CONSEGNATO.forMagento()
    case OrderStatus.STATO_ORDINE_ANNULLATO.forEglem():
        status = OrderStatus.STATO_ORDINE_ANNULLATO.forMagento()
print(status)
'''
