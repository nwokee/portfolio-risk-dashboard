## Purpose: collecting data from yfinance to use for calculations and visualizations
## Additional features: caching system to limit yfinance calls to stocks older than 1 day



import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


class DataCollector:

    # Initialize with cache directory
    def __init__(self, cache_dir="app/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    # Collect data only if needed (we dont have it in cache)
    def get_stock_data(self, symbol, period="2y"):
        cache_file = self.cache_dir / f"{symbol}_{period}.json"

    
        # check if file exists already (and is no older than a day)
        if cache_file.exists():
            # check cache age
            file_modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            cache_age = datetime.now() - file_modified_time
            # print(f"current cache age: {cache_age.total_seconds() / 3600:.1f} hours")

            if cache_age < timedelta(days=1):
                # cache is still relevant, load
                with open(cache_file, 'r') as f:
                    data_dict = json.load(f)
                
                df = pd.DataFrame(data_dict)

                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                
                # print(f"loaded rows: {len(df)}")
                return df
            # else, the cache file isnt relevant anymore, so treat it as if
            # it never existed

        #cache does not exist, get new data for the symbol
        # print(f"Fetching new data for {symbol}")
        
        try: 
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty:
                #no data found, return nothing
                # print(f"No data found for {symbol}")
                return None
            
            # save to cache for future use
            to_save = hist.reset_index()
            data_dict = to_save.to_dict(orient='records')

            with open(cache_file, 'w') as f:
                json.dump(data_dict, f, default=str)

            # print(f"saved to {cache_file}")
            return hist
        
        except Exception as e:
            print(f"Error collecting data for {symbol}: {e}")
            return None


    def get_stock_info(self, symbol):
        cache_file = self.cache_dir / f"{symbol}_info.json"

    
        # check if file exists already (and is no older than a day)
        if cache_file.exists():
            # check cache age
            file_modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            cache_age = datetime.now() - file_modified_time
            # print(f"current cache age: {cache_age.total_seconds() / 3600:.1f} hours")

            if cache_age < timedelta(days=7):
                # cache is still relevant, load
                with open(cache_file, 'r') as f:
                    return json.load(f)
            # else, the cache file isnt relevant anymore, so treat it as if
            # it never existed
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
        
        # Extract only info that would be needed
            relevant_info = {
                'symbol': symbol,
                'shortName': info.get('shortName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'marketCap': info.get('marketCap', 0),
                'country': info.get('country')
            }
        
            # save to cache for future use
            with open(cache_file, 'w') as f:
                json.dump(relevant_info, f)
        
            return relevant_info
        
        except Exception as e:
            print(f"Error fetching info for {symbol}: {e}")
            return {'symbol': symbol, 'shortName': symbol}

# Test the code
if __name__ == "__main__":
    print("=== Testing DataCollector ===\n")
    
    # Create collector
    collector = DataCollector()
    
    # Test with Apple stock
    print("\n--- First fetch (will download) ---")
    data1 = collector.get_stock_data("AAPL", "2y")
    
    if data1 is not None:
        print(f"\nData shape: {data1.shape}")
        print(f"\nFirst few rows:")
        print(data1.head())
        print(f"\nColumns: {data1.columns.tolist()}")
    
    # Test again (should use cache)
    print("\n\n--- Second fetch (should use cache) ---")
    data2 = collector.get_stock_data("AAPL", "2y")
    
    if data2 is not None:
        print(f"\nData shape: {data2.shape}")