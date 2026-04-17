## Purpose: Writes portfolio data to the InfluxDB bucket

from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os
from dotenv import load_dotenv


class InfluxWriter:
    
    def __init__(self, url=None, token=None, org=None, bucket=None):
        load_dotenv('docker/.env')

        self.url = url or os.getenv('INFLUXDB_URL') or 'http://localhost:8086'
        self.token = token or os.getenv('INFLUXDB_TOKEN')
        self.org = org or os.getenv('INFLUXDB_ORG')
        self.bucket = bucket or os.getenv('INFLUXDB_BUCKET')

        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

        print(f"Connected to InfluxDB at {self.url}")
    
    
    def write_portfolio_data(self, results, portfolio_name="default"):
        # writes out the portfolio data to InfluxDB


        print("Writing data to InfluxDB")

        total_points = 0

        # write individual stock data
        stock_points = self.write_stock_metrics(results['stocks'], portfolio_name)
        total_points += stock_points

        # write portfolio aggregate data
        portfolio_points = self.write_portfolio_metrics(results['portfolio'], portfolio_name)
        total_points += portfolio_points

        # write portfolio holdings
        holdings_points = self.write_holdings(results['stocks'], portfolio_name)
        total_points += holdings_points

        # Print summary
        print(f"Wrote {total_points} data points to InfluxDB")

        return total_points
    
    
    def write_stock_metrics(self, stocks_data, portfolio_name="default"):
        # writes individual stock metrics to InfluxDB

        points = []

        for symbol, data in stocks_data.items():

            # Write Beta
            beta_series = data['beta'].dropna()
            for date, value in beta_series.items():
                point = Point("stock_metrics") \
                    .tag("symbol", symbol) \
                    .tag("metric", "beta") \
                    .tag("portfolio", portfolio_name) \
                    .field("value", float(value)) \
                    .field("weight", float(data['weight'])) \
                    .time(date)
                
                points.append(point)

            # Write Alpha
            alpha_series = data['alpha'].dropna()
            for date, value in alpha_series.items():
                point = Point("stock_metrics") \
                    .tag("symbol", symbol) \
                    .tag("metric", "alpha") \
                    .tag("portfolio", portfolio_name) \
                    .field("value", float(value)) \
                    .field("weight", float(data['weight'])) \
                    .time(date)
                
                points.append(point)

            # Write Sharpe Ratio
            sr_series = data['sharpe'].dropna()
            for date, value in sr_series.items():
                point = Point("stock_metrics") \
                    .tag("symbol", symbol) \
                    .tag("metric", "sharpe") \
                    .tag("portfolio", portfolio_name) \
                    .field("value", float(value)) \
                    .field("weight", float(data['weight'])) \
                    .time(date)
                
                points.append(point)

            # Write Price
            price_series = data['prices'].dropna()
            for date, value in price_series.items():
                point = Point("stock_metrics") \
                    .tag("symbol", symbol) \
                    .tag("metric", "price") \
                    .tag("portfolio", portfolio_name) \
                    .field("value", float(value)) \
                    .field("weight", float(data['weight'])) \
                    .time(date)
                
                points.append(point)

        self.write_api.write(bucket=self.bucket, org=self.org, record=points)

        return len(points)


    def write_portfolio_metrics(self, portfolio_data, portfolio_name="default"):
        # Writes portfolio metrics to InfluxDB

        points = []

        for metric_name, metric_series in portfolio_data.items():
            metric_series = metric_series.dropna()
            
            if metric_name == 'returns':
                continue
            
            for date, value in metric_series.items():
                point = Point("portfolio_metrics") \
                    .tag("symbol", "PORTFOLIO") \
                    .tag("metric", metric_name) \
                    .tag("portfolio", portfolio_name) \
                    .field("value", float(value)) \
                    .time(date)
                points.append(point)
            
        self.write_api.write(bucket=self.bucket, org=self.org, record=points)

        return len(points)
    
    def write_holdings(self, stocks_data, portfolio_name="default"):
        #Write portfolio holdings information
        
        points = []
        current_time = datetime.now()
        
        for symbol, data in stocks_data.items():
            point = Point("portfolio_holdings") \
                .tag("symbol", symbol) \
                .tag("portfolio", portfolio_name) \
                .field("weight", float(data['weight'])) \
                .field("allocation", float(data.get('allocation', 0))) \
                .field("shares", float(data.get('shares', 0))) \
                .field("initial_price", float(data.get('initial_price', 0))) \
                .field("current_price", float(data.get('current_price', 0))) \
                .field("current_value", float(data.get('current_value', 0))) \
                .time(current_time)
            
            points.append(point)
        
        self.write_api.write(bucket=self.bucket, org=self.org, record=points)
        print(f"Wrote {len(points)} holdings records")
        return len(points)
    
    
    def close(self):
        self.client.close()
        print("InfluxDB connection closed")