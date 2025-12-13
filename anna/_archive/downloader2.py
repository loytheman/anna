from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import pandas as pd

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []
        self.data_received = threading.Event()
        
    def historicalData(self, reqId, bar):
        """Callback for receiving historical data bars"""
        self.data.append({
            'Date': bar.date,
            'Open': bar.open,
            'High': bar.high,
            'Low': bar.low,
            'Close': bar.close,
            'Volume': bar.volume
        })
        
    def historicalDataEnd(self, reqId, start, end):
        """Called when all historical data has been received"""
        print(f"Historical data download complete")
        print(f"Data period: {start} to {end}")
        self.data_received.set()
        
    def error(self, reqId, errorTime, errorCode, errorMsg, advancedOrderRejectJson=""):
        """Error handling callback"""
        print(f"Error {errorCode}: {errorMsg}")
        if errorCode in [162, 200, 504]:  # Connection errors
            self.data_received.set()

def create_contract(symbol, sec_type="STK", exchange="SMART", currency="USD"):
    """Create a contract object for the specified symbol"""
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = currency
    return contract

def get_historical_data(symbol="AAPL", duration="1 Y", bar_size="1 day"):
    """
    Retrieve historical data for a given symbol
    
    Parameters:
    - symbol: Stock ticker symbol (default: "AAPL")
    - duration: How far back to retrieve data (e.g., "1 Y", "6 M", "1 W")
    - bar_size: Size of each bar (e.g., "1 day", "1 hour", "5 mins")
    """
    # Initialize the API
    app = IBApi()
    
    # Connect to TWS or IB Gateway (default port 7497 for TWS paper trading)
    # Use port 7496 for TWS live trading or 4001/4002 for IB Gateway
    print("Connecting to Interactive Brokers...")
    app.connect("127.0.0.1", 7497, clientId=1)
    
    # Start the socket in a thread
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    
    # Wait for connection
    time.sleep(1)
    
    if not app.isConnected():
        print("Failed to connect to IBKR")
        return None
    
    print(f"Connected successfully. Requesting historical data for {symbol}...")
    
    # Create contract
    contract = create_contract(symbol)
    
    # Request historical data
    # endDateTime: empty string means current time
    # duration: how far back
    # barSize: granularity
    # whatToShow: TRADES, MIDPOINT, BID, ASK
    # useRTH: 1 for regular trading hours only, 0 for all hours
    app.reqHistoricalData(
        reqId=1,
        contract=contract,
        endDateTime="",
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow="TRADES",
        useRTH=1,
        formatDate=1,
        keepUpToDate=False,
        chartOptions=[]
    )
    
    # Wait for data to be received (timeout after 30 seconds)
    app.data_received.wait(timeout=30)
    
    # Disconnect
    app.disconnect()
    
    # Convert to DataFrame
    if app.data:
        df = pd.DataFrame(app.data)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        print(f"\nRetrieved {len(df)} data points")
        return df
    else:
        print("No data received")
        return None

if __name__ == "__main__":
    # Get historical data for AAPL
    df = get_historical_data(
        symbol="AAPL",
        duration="1 Y",      # 1 year of data
        bar_size="1 day"     # Daily bars
    )
    
    if df is not None:
        # Display first and last few rows
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nLast 5 rows:")
        print(df.tail())
        
        # Save to CSV
        filename = "AAPL_historical_data.csv"
        df.to_csv(filename)
        print(f"\nData saved to {filename}")
        
        # Basic statistics
        print("\nBasic Statistics:")
        print(df.describe())