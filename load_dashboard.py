## Purpose: Loads all portfolio templates to the dashboard
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from influxdb_client import InfluxDBClient
from portfolio_processor import PortfolioProcessor
from influx_writer import InfluxWriter
from dotenv import load_dotenv

load_dotenv('docker/.env')

def clear_influxdb():
    # clears out influxDB bucket
    print("Clearing InfluxDB data...")
    
    url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    token = os.getenv('INFLUXDB_TOKEN')
    org = os.getenv('INFLUXDB_ORG')
    bucket = os.getenv('INFLUXDB_BUCKET')
    
    client = InfluxDBClient(url=url, token=token, org=org, timeout=30000)
    delete_api = client.delete_api()
    
    try:
        delete_api.delete(
            start="1970-01-01T00:00:00Z",
            stop="2099-12-31T23:59:59Z",
            predicate='',
            bucket=bucket,
            org=org
        )
        print("Data cleared\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    client.close()


def load_portfolio(csv_path, name):
    # loads a single portfiolio (by csv)
    print(f"Loading the following portfolio: {name}")
    
    processor = PortfolioProcessor()
    portfolio = processor.load_portfolio(csv_path)
    
    if portfolio is None:
        print(f"✗ Failed to load portfolio CSV")
        return False
    
    results = processor.process_portfolio(portfolio, period="2y")
    
    if results is None:
        print(f"✗ Failed to process portfolio")
        return False
    
    writer = InfluxWriter()
    points = writer.write_portfolio_data(results, portfolio_name=name)
    writer.close()
    
    print(f"\n✓ {name} loaded successfully ({points} data points)\n")
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LOADING DASHBOARD")
    print("="*60 + "\n")
    
    # Clear existing data
    clear_influxdb()


    
    portfolios = [
        ("data/template-port.csv", "template"),
        ("data/custom-port.csv", "custom"),
        ("data/very-conservative-port.csv", "very-conservative"),
        ("data/conservative-port.csv", "conservative"),
        ("data/moderate-port.csv", "moderate"),
        ("data/risky-port.csv", "risky"),
        ("data/very-risky-port.csv", "very-risky"),
        ("data/tech-port.csv", "technology"),
        ("data/health-port.csv", "healthcare"),
        ("data/energy-port.csv", "energy"),
        ("data/consumer-port.csv", "consumer"),
        ("data/financial-port.csv", "finance"),

    ]

    for csv_path, name in portfolios:
        success = load_portfolio(csv_path, name)

        if success:
            print(f"{name} LOADED SUCCESSFULLY")
        else:
            print(f"{name} LOADING FAILED")