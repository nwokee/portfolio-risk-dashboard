## Purpose: loads portfolio from a csv and calculates the risk metrics for all stocks in the portfolio
## Feature: additionally creates weighted stock metrics for additional info

import pandas as pd
import numpy as np
from data_collector import DataCollector
from risk_calculations import RiskCalculator

class PortfolioProcessor:


    def __init__(self):
        data_coll = self.data_collector = DataCollector()
        risk_calc = self.risk_calculator = RiskCalculator()

    
    def load_portfolio(self, csv_path):

        # load and clean up portfolio for processing
        port = pd.read_csv(csv_path, sep=None, engine='python', header=None, 
                           names=['symbol', 'weight'], skipinitialspace=True)
    
        port['symbol'] = port['symbol'].str.strip()
        port['symbol'] = port['symbol'].str.upper()
        port['weight'] = port['weight'].astype(float)
    
        #DEBUGGING: Validation
        print(f"Loaded portfolio with {len(port)} stocks:")
        print(port.to_string(index=False))
        print(f"\nTotal weight: {port['weight'].sum():.2f}")


        # warning if weights don't add up to 1 (with room for error)
        if not (0.95 <= port['weight'].sum() <= 1.05):
            print("Warning: Weights don't sum to 1.0")

        return port

    def process_portfolio(self, portfolio_df, period="2y",initial_investment=5000):

        # collecting market data
        print("Fetching Market Data")
        market_data = self.data_collector.get_stock_data(symbol="^GSPC", period=period)
        if market_data is None:
            print("Error: No market data found for ^GSPC")
            return None
        
        market_returns = self.risk_calculator.calculate_returns(market_data)
        print("Successfully collected market data")


        results = {
            'stocks': {},
            'portfolio': {}
        }

        # processing all portfolio data
        for idx, row in portfolio_df.iterrows():

            symbol = row['symbol']
            weight = row['weight']

            print(f"Processing {symbol} ({idx+1}/{len(portfolio_df)})...")

            stock_data = self.data_collector.get_stock_data(symbol, period)
            if stock_data is None or stock_data.empty:
                print(f"Skipping {symbol} - no data available")
                continue

            stock_returns = self.risk_calculator.calculate_returns(stock_data)
            rolling_beta = self.risk_calculator.calculate_rolling_beta(stock_returns, market_returns)
            rolling_alpha = self.risk_calculator.calculate_rolling_alpha(stock_returns, market_returns)
            rolling_rs = self.risk_calculator.calculate_rolling_sharpe(stock_returns)

            allocation = initial_investment * weight 
            initial_price = stock_data['Close'].iloc[0]  
            num_shares = allocation / initial_price

            results['stocks'][symbol] = {
                'weight': weight,
                'prices': stock_data['Close'],
                'returns': stock_returns,
                'beta': rolling_beta,
                'alpha': rolling_alpha,
                'sharpe': rolling_rs,
                'allocation': allocation,
                'initial_price': initial_price,
                'shares': num_shares,
                'current_price': stock_data['Close'].iloc[-1],
                'current_value': num_shares * stock_data['Close'].iloc[-1]
            }

            print(f"{symbol} processed")

        
        print("Calculating portfolio returns and value...")
        
        # Calculate weighted portfolio returns
        portfolio_returns = None
        
        for symbol, data in results['stocks'].items():
            weighted_returns = data['returns'] * data['weight']
            
            if portfolio_returns is None:
                portfolio_returns = weighted_returns
            else:
                portfolio_returns = portfolio_returns.add(weighted_returns, fill_value=0)
        
        # Calculate portfolio value over time
        portfolio_value = self.risk_calculator.calculate_portfolio_value(
            portfolio_returns, 
            initial_value=initial_investment
        )
        
        # Store in results
        results['portfolio']['value'] = portfolio_value
        results['portfolio']['returns'] = portfolio_returns
        
        # Print final value
        final_value = portfolio_value.iloc[-1]
        initial_value = initial_investment
        total_return = ((final_value - initial_value) / initial_value) * 100
        
        print(f"\nPortfolio Performance:")
        print(f"  Initial Investment: ${initial_value:.2f}")
        print(f"  Final Value: ${final_value:.2f}")
        print(f"  Total Return: {total_return:.2f}%")  

        print("Calculating portfolio metrics")

        portfolio_beta = None
        portfolio_alpha = None
        portfolio_sr = None

        for symbol, data in results['stocks'].items():
            
            # weighted calculations
            weighted_beta = data['beta'] * data['weight']
            weighted_alpha = data['alpha'] * data['weight']
            weighted_sharpe = data['sharpe'] * data['weight']

            if portfolio_beta is None:
                portfolio_beta = weighted_beta
                portfolio_alpha = weighted_alpha
                portfolio_sr = weighted_sharpe
            else:
                portfolio_beta = portfolio_beta.add(weighted_beta, fill_value=0)
                portfolio_alpha = portfolio_alpha.add(weighted_alpha, fill_value=0)
                portfolio_sr = portfolio_sr.add(weighted_sharpe, fill_value=0)

        results['portfolio']['beta'] = portfolio_beta
        results['portfolio']['alpha'] = portfolio_alpha
        results['portfolio']['sharpe'] = portfolio_sr
        results['portfolio']['value'] = portfolio_value
        results['portfolio']['returns'] = portfolio_returns


        print(f"Processed {len(results['stocks'])} stocks")
        print(f"Latest Portfolio Beta: {portfolio_beta.iloc[-1]:.4f}")
        print(f"Latest Portfolio Alpha: {portfolio_alpha.iloc[-1]:.4f}")
        print(f"Latest Portfolio Sharpe Ratio: {portfolio_sr.iloc[-1]:.4f}")
        print(f"Latest Portfolio Value: ${portfolio_value.iloc[-1]:.2f}")

        return results

if __name__ == "__main__":
    processor = PortfolioProcessor()
    portfolio = processor.load_portfolio("data/test-portfolio.csv")
    port2 = processor.load_portfolio("data/test-port-2.csv")
    print("\nPortfolios loaded successfully!")
    
    results = processor.process_portfolio(portfolio, period="2y")
    
    if results:
        print("\n" + "="*50)
        print("Individual Stock Latest Values:")
        print("="*50)
        for symbol, data in results['stocks'].items():
            print(f"{symbol:6} - Beta: {data['beta'].iloc[-1]:6.3f}  "
                f"Alpha: {data['alpha'].iloc[-1]:7.3f}  "
                f"Sharpe: {data['sharpe'].iloc[-1]:6.3f}  " 
                f"Weight: {data['weight']:.2f}")