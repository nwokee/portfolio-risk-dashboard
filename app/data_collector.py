## Purpose: collecting data from yfinance to use for calculations and visualizations
## Additional features: caching system to limit yfinance calls to stocks older than 1 day

import yfinance as yf
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from risk_calculations import RiskCalculator


class DataCollector:

    # Initialize with cache directory
    def __init__(self, cache_dir="app/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    # Collect data only if needed (we dont have it in cache)
    def get_stock_data(self, symbol, period="2y", market_data=None):
        cache_file = self.cache_dir / f"{symbol}_{period}.json"

    
        # check if file exists already (and is no older than a day)
        if cache_file.exists():
            # check cache age
            file_modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            cache_age = datetime.now() - file_modified_time

            if cache_age < timedelta(days=1):
                # cache is still relevant, load
                with open(cache_file, 'r') as f:
                    data_dict = json.load(f)
                
                df = pd.DataFrame(data_dict)

                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'],utc=True)
                    df.set_index('Date', inplace=True)
                
                return df
            # else, the cache file isnt relevant anymore, so treat it as if
            # it never existed

        # cache does not exist, get new data for the symbol
        
        try: 
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty:
                #no data found, return nothing
                return None
            
            time.sleep(1) # delaying yfinance call to prevent yfinance rate limit

            to_save = hist.copy()

            # grab market data and add returns if needed
            if symbol != "^GSPC" and market_data is None:
                market_data = self.get_stock_data("^GSPC",period="2y")
                calculator = RiskCalculator()

                # calculate returns for stock and market
                s_returns = calculator.calculate_returns(hist)
                m_returns = calculator.calculate_returns(market_data)
                
                # calculate risk metrics
                s_beta = calculator.calculate_rolling_beta(s_returns, m_returns)
                s_alpha = calculator.calculate_rolling_alpha(s_returns, m_returns)
                s_sharpe = calculator.calculate_rolling_sharpe(s_returns)

                # add metrics to hist df (NaNs are fine at the beginning)
                to_save = pd.merge(to_save, s_returns, left_index=True, right_index=True, how='left')
                to_save['Beta'] = s_beta
                to_save['Alpha'] = s_alpha
                to_save['Sharpe'] = s_sharpe

        
            
            to_save = to_save.reset_index()
            data_dict = to_save.to_dict(orient='records')

            with open(cache_file, 'w') as f:
                json.dump(data_dict, f, default=str)

            return to_save
        
        except Exception as e:
            print(f"Error collecting data for {symbol}: {e}")
            return None

        
    def check_ticker(self, symbol):
        # checks if the given stock ticker exists
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            time.sleep(1)
            return not hist.empty
        except:
            return False