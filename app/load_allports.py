## Purpose: loads all my csvs, processes them, and writes them into the InfluxDB bucket

from influxdb_client import InfluxDBClient
from portfolio_processor import PortfolioProcessor
from influx_writer import InfluxWriter
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv('docker/.env')

def clear_influxdb():
    """Clear all data from InfluxDB"""
    print("Clearing InfluxDB data...")
    
    url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    token = os.getenv('INFLUXDB_TOKEN')
    org = os.getenv('INFLUXDB_ORG')
    bucket = os.getenv('INFLUXDB_BUCKET')
    
    client = InfluxDBClient(url=url, token=token, org=org)
    delete_api = client.delete_api()
    
    try:
        delete_api.delete(
            start="1970-01-01T00:00:00Z",
            stop="2099-12-31T23:59:59Z",
            predicate='',
            bucket=bucket,
            org=org
        )
        print("✓ Data cleared\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    client.close()


def load_portfolio(csv_path, name):
    # load a portfolio
    print(f"Loading: {name}")
    
    processor = PortfolioProcessor()
    portfolio = processor.load_portfolio(csv_path)
    results = processor.process_portfolio(portfolio)
    
    writer = InfluxWriter()
    writer.write_portfolio_data(results, portfolio_name=name)
    writer.close()
    
    print(f"{name} loaded successfully\n")

if __name__ == "__main__":

    print("Reloading All Portfolios")
    clear_influxdb()

    print("Loading all portfolios into InfluxDB")
    
    # Load all portfolios
    portfolios = [
        ("data/test-portfolio.csv", "0. test"),
        ("data/very-conservative-port.csv", "1. Very Low Risk Portfolio"),
        ("data/conservative-port.csv", "2. Low Risk Portfolio"),
        ("data/moderate-port.csv", "3. Moderate Risk Portfolio"),
        ("data/risky-port.csv", "4. High Risk Portfolio"),
        ("data/very-risky-port.csv", "5. Very High Risk Portfolio")
    ]
    
    for csv_path, name in portfolios:
        try:
            load_portfolio(csv_path, name)
        except Exception as e:
            print(f" Error loading {name}: {e}\n")
    
    print("All portfolios loaded")