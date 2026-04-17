## Purpose: loads portfolio from a csv and calculates the risk metrics for all stocks in the portfolio
## Feature: additionally creates weighted stock metrics for additional info

import pandas as pd
import numpy as np
from data_collector import DataCollector
from risk_calculations import RiskCalculator

class PortfolioProcessor:


    def __init__(self):
        self.data_collector = DataCollector()
        self.risk_calculator = RiskCalculator()

    
    def load_portfolio(self, csv_path):

        # load and clean up portfolio for processing
        port = pd.read_csv(csv_path, sep=None, engine='python', header=None, 
                           names=['symbol', 'weight'], skipinitialspace=True)
    
        port['symbol'] = port['symbol'].str.strip()
        port['symbol'] = port['symbol'].str.upper()
        port['weight'] = port['weight'].astype(float)
    
        print(f"Loaded portfolio with {len(port)} stocks:")
        print(port.to_string(index=False))
        print(f"\nTotal weight: {port['weight'].sum():.2f}")


        # warning if weights don't add up to 1 (with room for error)
        if not (0.95 <= port['weight'].sum() <= 1.05):
            print("Warning: Weights don't sum to 1.0")

        return port

    ## for aggregating data more efficiently
    def metric_matrices(self, stocks_data):

        returns_df = pd.DataFrame()
        beta_df = pd.DataFrame()
        alpha_df = pd.DataFrame()
        sharpe_df = pd.DataFrame()
        weights = {}



        for symbol, data in stocks_data.items():
            returns_df[symbol] = data['returns']
            beta_df[symbol] = data['beta']
            alpha_df[symbol] = data['alpha']
            sharpe_df[symbol] = data['sharpe']
            weights[symbol] = data['weight']
        
        weights = pd.Series(weights)

        return {
            "returns": returns_df,
            "beta": beta_df,
            "alpha": alpha_df,
            "sharpe": sharpe_df,
            "weights": weights
        }
    
    def metric_weighted_sum(self, df, weights):
        valid_mask = df.notna()
        valid_weight_sum = valid_mask.mul(weights, axis=1).sum(axis=1)
        weighted_values = df.mul(weights, axis=1)
        weighted_sum = weighted_values.sum(axis=1)
        result = weighted_sum / valid_weight_sum
        result[valid_weight_sum == 0] = np.nan
    
        return result




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

            # calculate holdings info
            allocation = initial_investment * weight 
            initial_price = stock_data['Close'].iloc[0]  
            num_shares = allocation / initial_price

            # collect and store all metrics and info
            results['stocks'][symbol] = {
                'weight': weight,
                'prices': stock_data['Close'],
                'returns': stock_data['Returns'].dropna(),
                'beta': stock_data['Beta'].dropna(),
                'alpha': stock_data['Alpha'].dropna(),
                'sharpe': stock_data['Sharpe'].dropna(),
                'allocation': allocation,
                'initial_price': initial_price,
                'shares': num_shares,
                'current_price': stock_data['Close'].iloc[-1],
                'current_value': num_shares * stock_data['Close'].iloc[-1]
            }

            print(f"{symbol} processed")

        
        print("Calculating portfolio returns and value...")
        
        # Calculate weighted portfolio returns
        weighted_port = self.metric_matrices(results['stocks'])
        returns_df = weighted_port['returns']
        beta_df = weighted_port['beta']
        alpha_df = weighted_port['alpha']
        sharpe_df = weighted_port['sharpe']
        weights = weighted_port['weights']
        
        portfolio_returns = returns_df.mul(weights, axis = 1).sum(axis = 1)
        portfolio_beta = self.metric_weighted_sum(beta_df, weights)
        portfolio_alpha = self.metric_weighted_sum(alpha_df, weights)
        portfolio_sr = self.metric_weighted_sum(sharpe_df, weights)


        # Calculate portfolio value over time
        portfolio_value = self.risk_calculator.calculate_portfolio_value(
            portfolio_returns, 
            initial_value=initial_investment
        )
        
        
        # Print final value
        final_value = portfolio_value.iloc[-1]
        initial_value = initial_investment
        total_return = ((final_value - initial_value) / initial_value) * 100
        
        print(f"\nPortfolio Performance:")
        print(f"  Initial Investment: ${initial_value:.2f}")
        print(f"  Final Value: ${final_value:.2f}")
        print(f"  Total Return: {total_return:.2f}%")  


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