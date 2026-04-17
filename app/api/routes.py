# Purpose: API routes for dashboard, as well as the models used

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
import sys
import os

# parent dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_processor import PortfolioProcessor
from metadata_storage import MetadataStorage
from influx_writer import InfluxWriter
from data_collector import DataCollector
import pandas as pd

router = APIRouter()


# Data Models
class Stock(BaseModel):
    # base stock
    symbol: str = Field(...)
    weight: float = Field(..., ge=0, le=1)

class Portfolio(BaseModel):
    # portfolio of stock
    port_id: str = Field(default="template", example="template")
    stocks: List[Stock]
    
    class Config:
        json_schema_extra = {
            "example": {
                "port_id": "template",
                "stocks": [
                    {"symbol": "AAPL", "weight": 0.25},
                    {"symbol": "MSFT", "weight": 0.25},
                    {"symbol": "GOOGL", "weight": 0.25},
                    {"symbol": "KO", "weight": 0.15},
                    {"symbol": "WMT", "weight": 0.10}
                ]
            }
        }

class UpdateResponse(BaseModel):
    # updated portfolio feedback
    success: bool
    message: str
    portfolio_id: str
    metrics: Dict = {}



# Routes

@router.get("/test")
async def test_endpoint():
    return {
        "status": "success",
        "message": "API is working",
        "test": True
    }


@router.get("/portfolio/{portfolio_id}/defaults")
async def get_portfolio_defaults(portfolio_id: str):
    # gets default weight for any template
    try:
        # default weights for each portfolio
        defaults = {
            "template": [
                {"symbol": "AAPL", "weight": 0.20},
                {"symbol": "MSFT", "weight": 0.20},
                {"symbol": "GOOGL", "weight": 0.20},
                {"symbol": "KO", "weight": 0.20},
                {"symbol": "WMT", "weight": 0.20}
            ],
            "custom": [
                {"symbol": "KO", "weight": 0.14},
                {"symbol": "ET", "weight": 0.09},
                {"symbol": "JNJ", "weight": 0.17},
                {"symbol": "MCD", "weight": 0.15},
                {"symbol": "AAPL", "weight": 0.11},
                {"symbol": "F", "weight": 0.18},
                {"symbol": "WMT", "weight": 0.16}
            ],
            "very-conservative": [
                {"symbol": "KO", "weight": 0.18},
                {"symbol": "PG", "weight": 0.16},
                {"symbol": "JNJ", "weight": 0.16},
                {"symbol": "PFE", "weight": 0.14},
                {"symbol": "WMT", "weight": 0.14},
                {"symbol": "T", "weight": 0.12},
                {"symbol": "XOM", "weight": 0.10}
            ],
            "conservative": [
                {"symbol": "AAPL", "weight": 0.15},
                {"symbol": "MSFT", "weight": 0.15},
                {"symbol": "KO", "weight": 0.12},
                {"symbol": "PG", "weight": 0.12},
                {"symbol": "JNJ", "weight": 0.12},
                {"symbol": "XOM", "weight": 0.12},
                {"symbol": "V", "weight": 0.11},
                {"symbol": "WMT", "weight": 0.11}
            ],
            "moderate": [
                {"symbol": "AAPL", "weight": 0.16},
                {"symbol": "MSFT", "weight": 0.16},
                {"symbol": "JPM", "weight": 0.14},
                {"symbol": "XOM", "weight": 0.12},
                {"symbol": "KO", "weight": 0.10},
                {"symbol": "UNH", "weight": 0.10},
                {"symbol": "HD", "weight": 0.10},
                {"symbol": "DIS", "weight": 0.12}
            ],
            "risky": [
                {"symbol": "AAPL", "weight": 0.18},
                {"symbol": "MSFT", "weight": 0.16},
                {"symbol": "GOOGL", "weight": 0.14},
                {"symbol": "AMZN", "weight": 0.14},
                {"symbol": "TSLA", "weight": 0.12},
                {"symbol": "NVDA", "weight": 0.12},
                {"symbol": "JPM", "weight": 0.14}
            ],
            "very-risky": [
                {"symbol": "NVDA", "weight": 0.22},
                {"symbol": "TSLA", "weight": 0.20},
                {"symbol": "AMZN", "weight": 0.18},
                {"symbol": "META", "weight": 0.15},
                {"symbol": "GOOGL", "weight": 0.15},
                {"symbol": "AAPL", "weight": 0.10}
            ],
            "technology": [
                {"symbol": "NVDA", "weight": 0.25},
                {"symbol": "MSFT", "weight": 0.20},
                {"symbol": "AAPL", "weight": 0.18},
                {"symbol": "META", "weight": 0.15},
                {"symbol": "GOOGL", "weight": 0.12},
                {"symbol": "AMD", "weight": 0.06},
                {"symbol": "PLTR", "weight": 0.04}
            ],
            "healthcare": [
                {"symbol": "LLY", "weight": 0.28},
                {"symbol": "UNH", "weight": 0.22},
                {"symbol": "JNJ", "weight": 0.16},
                {"symbol": "ABBV", "weight": 0.14},
                {"symbol": "MDT", "weight": 0.10},
                {"symbol": "MRNA", "weight": 0.06},
                {"symbol": "ISRG", "weight": 0.04}
            ],
            "energy": [
                {"symbol": "XOM", "weight": 0.24},
                {"symbol": "CVX", "weight": 0.20},
                {"symbol": "COP", "weight": 0.17},
                {"symbol": "NEE", "weight": 0.15},
                {"symbol": "SLB", "weight": 0.12},
                {"symbol": "ENPH", "weight": 0.08},
                {"symbol": "BKR", "weight": 0.04}
            ],
            "consumer": [
                {"symbol": "WMT", "weight": 0.20},
                {"symbol": "COST", "weight": 0.20},
                {"symbol": "KO", "weight": 0.15},
                {"symbol": "PEP", "weight": 0.15},
                {"symbol": "NKE", "weight": 0.15},
                {"symbol": "SBUX", "weight": 0.15}
            ],
            "finance": [
                {"symbol": "L", "weight": 0.26},
                {"symbol": "JPM", "weight": 0.22},
                {"symbol": "V", "weight": 0.18},
                {"symbol": "GS", "weight": 0.14},
                {"symbol": "AXP", "weight": 0.10},
                {"symbol": "SCHW", "weight": 0.06},
                {"symbol": "SQ", "weight": 0.04}
            ]
        }
        
        if portfolio_id in defaults:
            return {
                "portfolio_id": portfolio_id,
                "stocks": defaults[portfolio_id]
            }
        else:
            raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/portfolio/{portfolio_id}/weights")
async def get_portfolio_weights(portfolio_id: str):
    # gets weight for any specific portfolio
    try:
        storage = MetadataStorage()
        
        # Try to load from metadata
        weights = storage.get_port_weights(portfolio_id)
        
        if weights:
            return {
                "portfolio_id": portfolio_id,
                "stocks": weights
            }
        
        return await get_portfolio_defaults(portfolio_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portfolio/update-weights", response_model=UpdateResponse)
async def update_portfolio_weights(portfolio: Portfolio):
    # Update portfolio weights and recalculate portfolio metrics
    try:
        port_id = portfolio.port_id

        # Validate weights
        total_weight = sum(s.weight for s in portfolio.stocks)
        if not (0.995 <= total_weight <= 1.005):
            raise HTTPException(
                status_code=400, 
                detail=f"Weights sum to {total_weight:.2f}, must sum to 1"
            )
        
        # Filter out stocks with no weight
        stocks_to_process = [s for s in portfolio.stocks if s.weight > 0]
        if not stocks_to_process:
            raise HTTPException(status_code=400, detail="Portfolio must have at least one stock")
        
        storage = MetadataStorage()
        current = storage.get_port_weights(port_id) or []
        current_symbols = {s['symbol'] for s in current}
        new_symbols = {s.symbol.upper() for s in stocks_to_process}
        removed = current_symbols - new_symbols

        if removed:
            from influxdb_client import InfluxDBClient
            client = InfluxDBClient(
                url=os.getenv('INFLUXDB_URL'),
                token=os.getenv('INFLUXDB_TOKEN'),
                org=os.getenv('INFLUXDB_ORG'),
                timeout=30000
            )
            delete_api = client.delete_api()
            for symbol in removed:
                print(f"Deleting InfluxDB data for removed stock: {symbol}")
                
                # delete from stock_metrics
                delete_api.delete(
                    start="1970-01-01T00:00:00Z",
                    stop="2099-12-31T23:59:59Z",
                    predicate=f'_measurement="stock_metrics" AND symbol="{symbol}" AND portfolio="{port_id}"',
                    bucket=os.getenv('INFLUXDB_BUCKET'),
                    org=os.getenv('INFLUXDB_ORG')
                )
                
                # delete from portfolio_holdings
                delete_api.delete(
                    start="1970-01-01T00:00:00Z",
                    stop="2099-12-31T23:59:59Z",
                    predicate=f'_measurement="portfolio_holdings" AND symbol="{symbol}" AND portfolio="{port_id}"',
                    bucket=os.getenv('INFLUXDB_BUCKET'),
                    org=os.getenv('INFLUXDB_ORG')
                )
            
            client.close()
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {"symbol": s.symbol.upper(), "weight": s.weight}
            for s in stocks_to_process
        ])
        
        # Process portfolio
        processor = PortfolioProcessor()
        results = processor.process_portfolio(df, period="2y", initial_investment=5000)
        
        if results is None:
            raise HTTPException(status_code=500, detail="Failed to process portfolio")
        
        # Write to InfluxDB
        writer = InfluxWriter()
        points = writer.write_portfolio_data(results, portfolio_name=port_id)
        writer.close()
        


        # Save to metadata store
        storage.save_portfolio(
            port_id=port_id,
            stocks=[{"symbol": s.symbol, "weight": s.weight} for s in portfolio.stocks]
        )
        
        # Extract latest metrics
        latest_metrics = {
            "beta": float(results['portfolio']['beta'].iloc[-1]),
            "alpha": float(results['portfolio']['alpha'].iloc[-1]),
            "sharpe": float(results['portfolio']['sharpe'].iloc[-1]),
            "value": float(results['portfolio']['value'].iloc[-1]),
            "return_pct": float(
                ((results['portfolio']['value'].iloc[-1] - 5000) / 5000) * 100
            )
        }
        
        return UpdateResponse(
            success=True,
            message=f"{port_id} portfolio updated with {len(portfolio.stocks)} stocks",
            portfolio_id=port_id,
            metrics=latest_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/{portfolio_id}/add-stock")
async def add_stock(portfolio_id: str, stock: Stock):
    try:
        cache_file = Path(f"app/cache/{stock.symbol.upper()}_2y.json")
        is_new_ticker = not cache_file.exists()


        # make sure ticker exists
        collector = DataCollector()
        if not collector.check_ticker(stock.symbol.upper()):
            raise HTTPException(status_code=400, detail=f"{stock.symbol} is not a valid ticker")
        
        # Load current weights
        storage = MetadataStorage()
        weights = storage.get_port_weights(portfolio_id)
        
        if weights is None:
            # fall back to defaults if no metadata yet
            defaults = await get_portfolio_defaults(portfolio_id)
            weights = defaults['stocks']
        
        # Check if ticker already exists
        symbols = [s['symbol'] for s in weights]
        if stock.symbol.upper() in symbols:
            raise HTTPException(status_code=400, detail=f"{stock.symbol} is already in portfolio")
        
        # Add new stock at default 10% 
        weights.append({"symbol": stock.symbol.upper(), "weight": stock.weight})
        
        storage.save_portfolio(port_id=portfolio_id, stocks=weights)
        
        return {"success": True, "stocks": weights, "is_new_ticker": is_new_ticker}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))