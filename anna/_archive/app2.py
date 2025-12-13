from ibapi.client import *
from ibapi.wrapper import *
import time
import threading
import OrderSamples
import ContractType

class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.positions = []

    def nextId(self):
        self.orderId += 1
        return self.orderId

    def nextValidId(self, orderId):
        print(app.isConnected())
        self.orderId = orderId

    def contractDetails(self, reqId: int, contractDetails: ContractDetails): 
        print(contractDetails.contract)


    def openOrder(self, orderId, contract, order, orderState): 
        print(orderId, contract)
    
    def openOrderEnd(self):
        print("OpenOrderEnd")


    def position(self, account: str, contract: Contract, pos: float, avgCost: float):
        super().position(account, contract, pos, avgCost)
        self.positions.append({
            "account": account,
            "symbol": contract.symbol,
            "secType": contract.secType,
            "currency": contract.currency,
            "position": pos,
            "avgCost": avgCost
        })
        print(f"Position: Account={account}, Symbol={contract.symbol}, Pos={pos}, AvgCost={avgCost}")


    def test(self):
        mycontract = Contract()
        mycontract.conId = 265598
        mycontract.exchange = "SMART"

        myorder = Order()
        myorder.action = "BUY"
        # myorder.orderType = "MKT"
        myorder.orderType = "LMT"
        myorder.tif = "GTC"
        myorder.lmtPrice = 260
        myorder.totalQuantity = 1

        self.placeOrder(self.nextId(), mycontract, myorder)

        # ocaOrders = [OrderSamples.LimitOrder("BUY", 1, 10), OrderSamples.LimitOrder("BUY", 1, 11),
        #              OrderSamples.LimitOrder("BUY", 1, 12)]
        # OrderSamples.OneCancelsAll("TestOCA_" + str(self.nextValidId), ocaOrders, 2)
        # for o in ocaOrders:
        #     self.placeOrder(self.nextId(), mycontract, o)

        # bracket = OrderSamples.BracketOrder(self.nextId(), "BUY", 100, 30, 40, 20)
        # for o in bracket:
        #     self.placeOrder(o.orderId, mycontract, o)
            # self.nextId() 

        for i in range(1, 5):
            time.sleep(1)
            myorder.lmtPrice = 270 + i  
            # Self.placeOrder(self.orderId, mycontract, myorder)
            self.placeOrder(self.nextId(), mycontract, myorder)

        
        
        


app = TestApp()
app.connect("127.0.0.1", 7497, 0)
threading.Thread(target=app.run).start()
time.sleep(1)

app.reqAutoOpenOrders(True)
app.reqAllOpenOrders()
app.reqPositions() 


# app.reqGlobalCancel(OrderCancel())
# app.test()


