from ibapi.client import *
from ibapi.wrapper import *
import time
import threading
from ContractSamples import ContractSamples
from ContractType import ContractType

class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId):
        self.orderId = orderId

    def nextId(self):
        self.orderId += 1
        return self.orderId

    def contractDetails(self, reqId, contractDetails):
        attrs = vars(contractDetails)
        # print("\n".join(f"{name}:{value}" for name,value in attrs.items()))
        print(contractDetails.contract)

    def contractDetailsEnd(self, reqId: int):
        print("-----===== End of contract details =====-----")
        self.disconnect()
        # return super().contractDetailsEnd(reqId)

    def error(self, reqId, errorTime, errorCode, errorString, advancedOrderRejectJson):
        print(f"reqId: {reqId}, errorTime: {errorTime},  errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}")


    def test(self, c:Contract):
        print(">>>")
        app.reqContractDetails(app.nextId(), c)
        



app = TestApp()
app.connect("127.0.0.1", 7497, 888)
threading.Thread(target=app.run).start()
time.sleep(1)

# for i in range(0,5):
#     print(app.nextId())
#     app.reqCurrentTime()

mycontract = Contract()
# Stock
# mycontract.conId = 265598
# mycontract.symbol = "AAPL"
# mycontract.secType = "STK"
# mycontract.currency = "USD"
# mycontract.exchange = "SMART"
# mycontract.primaryExchange = "NASDAQ"

# Future
mycontract.conId = 495512563
# mycontract.symbol = "ES"
# mycontract.secType = "FUT"
# mycontract.currency = "USD"
# mycontract.exchange = "CME"
# mycontract.lastTradeDateOrContractMonth = "202512"

# Option
# mycontract.symbol = "SPX"
# mycontract.secType = "OPT"
# mycontract.currency = "USD"
# mycontract.exchange = "SMART"
# mycontract.lastTradeDateOrContractMonth = "202512"
# mycontract.right = "PUT"
# mycontract.tradingClass = "SPXW"
# mycontract.strike = "6800"

# app.test(mycontract)
app.test(ContractType.ES2603)


time.sleep(1)




