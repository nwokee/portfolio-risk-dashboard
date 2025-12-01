## Purpose: calculate risk metrics for a given stock portfolio on a rolling 3 month timescale
## Notes: every month is about 21 market days, so using 63 days for 3 months


import pandas as pd
import numpy as np


class RiskCalculator:


    def __init__(self, market_symbol="^GSPC"):
        # initialize risk calculator
        self.market_symbol = market_symbol


    def calculate_returns(self, price_data):
        # calculates daily returns from price data
        returns = price_data['Close'].pct_change().dropna()
        return returns

    def calculate_rolling_beta(self, stock_returns, market_returns,
                                window = 63):
        # calculates the rolling beta over a time period
        
        ## Align the two return series to same dates
        stock_returns = stock_returns.reindex(market_returns.index).dropna()
        
        ## Create empty list to store beta values
        rolling_betas = []
        
        # Loop through each day
        for i in range(len(stock_returns)):
            if i < window:
                # Not enough data yet, append NaN
                rolling_betas.append(np.nan)
            else:
                # Get window of returns
                stock_window = stock_returns.iloc[i-window+1:i+1]
                market_window = market_returns.iloc[i-window+1:i+1]
                
                # Calculate covariance and variance
                covariance = np.cov(stock_window, market_window)[0][1]
                variance = np.var(market_window)
                
                # Calculate beta
                if variance != 0:
                    beta = covariance / variance
                else:
                    beta = np.nan
                
                rolling_betas.append(beta)
        
        # Convert to Series with same index as stock_returns
        beta_series = pd.Series(rolling_betas, index=stock_returns.index)
        return beta_series

    def calculate_rolling_alpha(self, stock_returns, market_returns, 
                               risk_free_rate = 0.02, window = 63):
        # calculates rolling alpha over a time window

        ## calculate rolling betas
        betas = self.calculate_rolling_beta(stock_returns, market_returns, window)
        stock_returns = stock_returns.reindex(market_returns.index).dropna()

        
        ## create an empty list for alpha values
        rolling_alphas = []
        daily_rf = risk_free_rate / 252

        ## loop through every day
        for i in range(len(stock_returns)):
            if i < window:
                # Not enough data yet, append NaN
                rolling_alphas.append(np.nan)
            else:
                # Get window of returns
                stock_window = stock_returns.iloc[i-window+1:i+1]
                market_window = market_returns.iloc[i-window+1:i+1]
                beta = betas.iloc[i]

                # Calculate alpha
                if beta is not np.nan:
                    s_avg = stock_window.mean()
                    m_avg = market_window.mean()

                    s_excess = s_avg - daily_rf
                    m_excess = m_avg - daily_rf

                    alpha = s_excess - (beta * m_excess)

                    alpha *= 252
                else:
                    alpha = np.nan

                rolling_alphas.append(alpha)

        ## convert to series and return
        alpha_series = pd.Series(rolling_alphas, index=stock_returns.index)
        return alpha_series

    def calculate_rolling_sharpe(self, stock_returns, 
                                        risk_free_rate=0.02, window=63):
        #calculates rolling sharpe ratio over a time window

        daily_rf = risk_free_rate / 252

        rolling_sr = []

         # Loop through each day
        for i in range(len(stock_returns)):
            if i < window:
                # Not enough data yet
                rolling_sr.append(np.nan)
            else:
                # Get window of returns
                returns_window = stock_returns.iloc[i-window+1:i+1]
                
                # Calculate statistics
                mean_return = returns_window.mean()
                std_return = returns_window.std()
                
                # Calculate Sharpe ratio
                if std_return != 0:
                    excess_return = mean_return - daily_rf
                    sharpe = excess_return / std_return
                    # Annualize
                    sharpe_annual = sharpe * np.sqrt(252)
                else:
                    sharpe_annual = np.nan

                rolling_sr.append(sharpe_annual)

        # Return as Series
        return pd.Series(rolling_sr, index=stock_returns.index)
    
    def calculate_portfolio_value(self, portfolio_returns, initial_value=1000):
        # calculates the portfolio value over time given returns and initial value
        values = []
        current_value = initial_value
        
        # Calculate value day by day
        for daily_return in portfolio_returns:
            current_value = current_value * (1 + daily_return)
            values.append(current_value)
        
        # Return as Series with same index as returns
        return pd.Series(values, index=portfolio_returns.index)


if __name__ == "__main__":
    from data_collector import DataCollector
    
    collector = DataCollector()
    calculator = RiskCalculator()
    
    print("Fetching data...")
    aapl_data = collector.get_stock_data("AAPL", "2y")  # Use 2 years
    market_data = collector.get_stock_data("^GSPC", "2y")
    
    print("\nCalculating returns...")
    aapl_returns = calculator.calculate_returns(aapl_data)
    market_returns = calculator.calculate_returns(market_data)
    
    print("\nCalculating rolling beta...")
    beta = calculator.calculate_rolling_beta(aapl_returns, market_returns)
    
    print("\nCalculating rolling alpha...")
    alpha = calculator.calculate_rolling_alpha(aapl_returns, market_returns)
    
    print(f"\n=== Results ===")
    print(f"Latest Beta: {beta.iloc[-1]:.3f}")
    print(f"Average Beta: {beta.mean():.3f}")
    print(f"\nLatest Alpha: {alpha.iloc[-1]:.3f}")
    print(f"Average Alpha: {alpha.mean():.3f}")
    
    print(f"\nLast 10 Beta values:")
    print(beta.tail(10))

    print(f"\nLast 10 Alpha values:")
    print(alpha.tail(10))