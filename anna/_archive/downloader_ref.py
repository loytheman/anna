"""
IBKR Historical Data Downloader
Requirements: pip install ib_insync pandas
"""

from ib_insync import IB, Stock, Forex, util
import pandas as pd
from datetime import datetime, timedelta
import time

class IBKRDataDownloader:
    def __init__(self, host='127.0.0.1', port=7497, client_id=0):
        """
        Initialize IBKR connection
        
        Args:
            host: TWS/Gateway host (default: localhost)
            port: 7497 for TWS paper, 7496 for TWS live, 4002 for Gateway paper, 4001 for Gateway live
            client_id: Unique client identifier
        """
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        
    def connect(self):
        """Connect to TWS or IB Gateway"""
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            print(f"Connected to IBKR on {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        self.ib.disconnect()
        print("Disconnected from IBKR")
    
    def download_stock_data(self, symbol, exchange='SMART', currency='USD',
                           duration='1 Y', bar_size='1 day', what_to_show='TRADES',
                           end_date=''):
        """
        Download historical data for a stock
        
        Args:
            symbol: Stock ticker symbol
            exchange: Exchange (default: SMART for smart routing)
            currency: Currency (default: USD)
            duration: Time period (e.g., '1 Y', '6 M', '1 W', '1 D')
            bar_size: Bar size (e.g., '1 day', '1 hour', '5 mins', '1 min')
            what_to_show: Data type (TRADES, MIDPOINT, BID, ASK)
            end_date: End date (format: 'YYYYMMDD HH:MM:SS'), empty string for now
        
        Returns:
            pandas DataFrame with historical data
        """
        # Create contract
        contract = Stock(symbol, exchange, currency)
        
        # Qualify the contract
        self.ib.qualifyContracts(contract)
        
        # Request historical data
        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime=end_date,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=True,  # Regular trading hours only
            formatDate=1
        )
        
        # Convert to DataFrame
        df = util.df(bars)
        
        if not df.empty:
            df['symbol'] = symbol
            print(f"Downloaded {len(df)} bars for {symbol}")
        else:
            print(f"No data received for {symbol}")
        
        return df
    
    def download_forex_data(self, pair='EURUSD', duration='1 Y', 
                           bar_size='1 day', what_to_show='MIDPOINT'):
        """
        Download historical data for forex pair
        
        Args:
            pair: Currency pair (e.g., 'EURUSD', 'GBPUSD')
            duration: Time period
            bar_size: Bar size
            what_to_show: MIDPOINT, BID, or ASK
        
        Returns:
            pandas DataFrame with historical data
        """
        # Create forex contract
        contract = Forex(pair)
        
        # Request historical data
        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=False,  # Forex trades 24/5
            formatDate=1
        )
        
        # Convert to DataFrame
        df = util.df(bars)
        
        if not df.empty:
            df['pair'] = pair
            print(f"Downloaded {len(df)} bars for {pair}")
        
        return df
    
    def download_multiple_stocks(self, symbols, **kwargs):
        """
        Download data for multiple stocks with rate limiting
        
        Args:
            symbols: List of stock symbols
            **kwargs: Additional arguments passed to download_stock_data
        
        Returns:
            Dictionary of DataFrames keyed by symbol
        """
        data = {}
        
        for i, symbol in enumerate(symbols):
            try:
                df = self.download_stock_data(symbol, **kwargs)
                data[symbol] = df
                
                # Rate limiting: IBKR has strict request limits
                if i < len(symbols) - 1:
                    time.sleep(1)  # Wait 1 second between requests
                    
            except Exception as e:
                print(f"Error downloading {symbol}: {e}")
                data[symbol] = pd.DataFrame()
        
        return data
    
    def save_to_csv(self, df, filename):
        """Save DataFrame to CSV file"""
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")


# Example usage
if __name__ == "__main__":
    # Initialize downloader
    downloader = IBKRDataDownloader(
        host='127.0.0.1',
        port=7497,  # TWS paper trading port
        client_id=1
    )
    
    # Connect to IBKR
    if downloader.connect():
        try:
            # Example 1: Download single stock
            print("\n--- Downloading AAPL data ---")
            aapl_data = downloader.download_stock_data(
                symbol='AAPL',
                duration='1 Y',
                bar_size='1 day'
            )
            print(aapl_data.head())
            
            # Save to CSV
            if not aapl_data.empty:
                downloader.save_to_csv(aapl_data, 'aapl_historical.csv')
            
            # Example 2: Download multiple stocks
            print("\n--- Downloading multiple stocks ---")
            symbols = ['AAPL', 'MSFT', 'GOOGL']
            multi_data = downloader.download_multiple_stocks(
                symbols,
                duration='6 M',
                bar_size='1 day'
            )
            
            # Example 3: Download forex data
            print("\n--- Downloading EURUSD data ---")
            forex_data = downloader.download_forex_data(
                pair='EURUSD',
                duration='1 M',
                bar_size='1 hour'
            )
            print(forex_data.head())
            
        finally:
            # Always disconnect
            downloader.disconnect()
    else:
        print("Failed to connect to IBKR. Make sure TWS or IB Gateway is running.")