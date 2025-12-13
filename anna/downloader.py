from ibapi.client import *
from ibapi.wrapper import *
import time
import threading
import pandas as pd
from ContractType import ContractType

class DownloaderApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []
        self.evt_data_received = threading.Event()

    def historicalData(self, reqId, bar):
        """Callback for receiving historical data bars"""
        self.data.append({'Date': bar.date,'Open': bar.open,'High': bar.high,'Low': bar.low,'Close': bar.close,'Volume': bar.volume})
        # print(bar)

    def historicalDataEnd(self, reqId, start, end):
        """Called when all historical data has been received"""
        print(f"Historical data download complete")
        print(f"Data period: {start} to {end}")
        self.evt_data_received.set()


    def download_stock_data(self, contract, duration='1 Y', bar_size='1 day', what_to_show='TRADES', end_date=''):
        self.reqHistoricalData(
            reqId=1,
            contract=contract,
            endDateTime=end_date,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=True,  # Regular trading hours only
            formatDate=1,
            keepUpToDate=True,
            chartOptions=[]
        )

        self.evt_data_received.wait(timeout=30)
        if self.data:
            df = pd.DataFrame(self.data)
            print("???")
            # df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d %H:%M:%S %Z')
            df['Date'] = pd.to_datetime(df['Date'].str[:17])
            df.set_index('Date', inplace=True)
            print(f"OK! Retrieved {len(df)} data points")
            return df
        else:
            print("ERROR! No data received")
            return None
        


app = DownloaderApp()
app.connect("127.0.0.1", 7497, 0)
threading.Thread(target=app.run).start()
time.sleep(1)

print("app.isConnected()",app.isConnected())

if not app.isConnected():
    print("ERROR! Failed to connect to IBKR...")
    print("Exiting progam.")
    sys.exit(0)

# c = ContractType.ES2603
c = ContractType.ES2512
duration = '3 M'
bar_size = "1 hour"

print(f"\nConnected successfully. Requesting historical data for {c.symbol}({c.conId}) ...")
historicalData = app.download_stock_data(c, duration=duration, bar_size=bar_size)

if historicalData is not None:
    # Save to CSV
    filename = f"{c.symbol}({c.conId})({bar_size})({duration})_historical_data.csv"
    historicalData.to_csv(filename)

app.disconnect()

