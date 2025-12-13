# Contract Id
from ibapi.client import *

def getContract(conId, symbol, secType="STK", currency="USD", exchange="SMART", primaryExchange=""):
    c = Contract()
    c.conId = conId
    c.symbol = symbol
    c.secType = secType
    c.currency = currency
    c.exchange = exchange
    c.primaryExchange = primaryExchange
    return c


# ES MINI --> H: March, M: June, U: September, Z: December 

class ContractType:
    # APPLE
    AAPL = getContract(265598, "AAPL", "STK", "USD", "SMART", "NASDAQ")
    # ESZ5
    ES2512 = getContract(495512563, "ES", "FUT", "USD", "CME")
    # ESH6
    ES2603 = getContract(649180695, "ES", "FUT", "USD", "CME")




