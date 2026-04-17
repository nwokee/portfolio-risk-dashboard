# Portfolio Risk Analysis Dashboard

This project is an interactive portfolio risk dashboard that collects historical stock data, computes the risk metrics, and displays them on a Grafana dashboard. Users can access multiple portfolio templates and tailor each to their liking.

Built with Python, FastAPI, InfluxDB, and Grafana.

---

## Prerequisites

Before getting started, install the following tools:

- **Python 3.10 or higher:** https://www.python.org/downloads/
  - During installation, check **"Add Python to PATH"** before clicking Install
- **Docker Desktop:** https://www.docker.com/products/docker-desktop/
---

## Installation & Setup

### Step 1: Get the Project Files
Unzip the file to a location on your computer that is easy to find, such as your Desktop or Documents folder. Then open a terminal and navigate into the project folder:

On Windows:
```
cd C:\Users\YourName\Desktop\portfolio-risk-dashboard
```

On Mac:
```
cd /Users/YourName/Desktop/portfolio-risk-dashboard
```

---

### Step 2: Install Python Dependencies

First, create a virtual environment to keep the project's dependencies isolated from the rest of your system. Run the following commands in order from inside the project folder:
 
**Create the virtual environment:**
```
python -m venv .venv
```
 
**Activate it:**
 
On Mac:
```
source .venv/bin/activate
```
 
On Windows:
```
.venv\Scripts\activate
```
 
You should see `(.venv)` appear at the start of your terminal prompt, confirming the environment is active.
 
**Install dependencies:**
```
pip install -r requirements.txt
```

This may take a minute to complete.

---

### Step 3: Start Docker Containers

Run the following 2 commands to start InfluxDB and Grafana:

```
cd docker
docker compose up -d
```

Wait a little for it to finish on the first instance. Once it is done it will be running in the background, and you can run
```
cd ..
```

---


### Step 4: Connect Grafana to InfluxDB

Open your browser and go to:

```
http://localhost:3000
```

Log in with username `admin` and password `admin`. You will be prompted to set a new password.

Navigate to **Connections -> Data Sources**, click **Add Data Source**, and select **InfluxDB**. Configure it with these 5 settings:

| Setting | Value |
|---|---|
| Query Language | Flux |
| URL | `http://influxdb:8086` |
| Organization | `risklab` |
| Token | `evensimplertoken` |
| Default Bucket | `market` |

You can ignore everything else, and then scroll down and click **Save & Test**. You should see a green confirmation message.

Once saved, look at the URL in your browser. It will look something like:
```
http://localhost:3000/connections/datasources/edit/abc123xyz
```
Copy the ID at the end of the URL; you will need it in the next step.

---

### Step 5: Import the Grafana Dashboard

Before importing, you need to update the dashboard file with your Grafana UID to prevent a connection error after import.

**5a: Update the dashboard file**
Open `grafana/dashboard.json` in any text editor. Use Find and Replace to find `INSERT_DASHBOARD_UID` and replace all instances with the UID you copied at the end of Step 4. Save the file.
 
**5b: Import the dashboard**
In Grafana, navigate to **Dashboards. Click **New** on the top right, then **Import**. Click **Upload JSON file** and select the updated `grafana/dashboard.json` from the project folder. 

The dashboard will appear but will show no data yet.

---

### Step 6: Load Portfolio Data

In your terminal, run:

```
python load_dashboard.py
```

This will process all portfolio CSV files, calculate rolling risk metrics for every stock, and write the results to InfluxDB. The process takes several minutes as it downloads up to two years of price history per stock. Progress will be printed to the terminal as each portfolio loads.

When you see **"All portfolios loaded"** the data is ready.

---

### Step 7: Start the API Server

In your terminal, run:

```
python run_api.py
```

Leave this terminal window open. The API must be running at all times for the weight adjustment panel to work. You should see a confirmation that the server is running at `http://localhost:8000`.

---

### Step 8: Open the Dashboard

Go back to Grafana at `http://localhost:3000`, navigate to **Dashboards**, and open the **Portfolio Risk Dashboard**. All panels should now be populated with data.

The dashboard is now ready to use.

---

## Usage

All interactions happen directly in Grafana. You do not need to touch any code after completing setup.

---

### Selecting a Portfolio

Use the **Portfolio** dropdown at the top of the dashboard to switch between profiles. All panels update automatically. The available portfolios are:

| Portfolio | Description |
|---|---|
| Template | Balanced five-stock starter portfolio |
| Custom | Personally curated portfolio |
| Very Conservative | Low-risk, stable holdings |
| Conservative | Mostly stable with some growth exposure |
| Moderate | Balanced risk and growth |
| Risky | Growth-oriented, higher volatility |
| Very Risky | Aggressive, high-volatility holdings |
| Technology | Major tech sector stocks |
| Healthcare | Major healthcare sector stocks |
| Energy | Major energy sector stocks |
| Consumer | Major consumer sector stocks |
| Finance | Major financial sector stocks |

---

### Understanding the Panels


**Beta Panel**
Shows how sensitive each stock and the overall portfolio are to market movement. A beta above 1.0 means the portfolio moves more than the market. A beta below 1.0 means it is more stable.

**Alpha Panel**
Shows whether each stock and the portfolio are outperforming the market on a risk-adjusted basis. Positive alpha means outperformance. Negative alpha means underperformance.

**Sharpe Ratio Panel**
Shows the return generated per unit of risk. A higher value means better risk-adjusted performance. A ratio above 1.0 is generally considered good.

The three panels above all display colored lines per stock and a bold white line for the overall portfolio average. Click any stock name in the legend to isolate its line, and shift click any stock name to toggle its appearance. To reset the view, double click any stock name

**Portfolio Value Panel**
Shows how a hypothetical $5,000 investment would have grown or declined over the past two years for the selected portfolio.

**Holdings Panel**
Shows the current composition of the portfolio in table form, including each stock's weight, dollar allocation, share count, current price, and current value.

---

### Adjusting Portfolio Weights

At the bottom of the dashboard is the **Edit Portfolio** panel.

1. Use the sliders or number inputs to adjust each stock's weight
2. The **Total Weight** display shows the current sum — it must reach exactly **100%** before you can submit
3. Click **Update Portfolio** to apply changes

The system will recalculate all metrics and refresh the dashboard automatically. This takes approximately 10–30 seconds.

---

### Adding a Stock

In the **Add Stock** section of the Edit Portfolio panel:

1. Type a valid ticker symbol into the input field (e.g. `NVDA`, `AMZN`)
2. Click **+ Add**

The system validates the ticker before adding it. If valid, the stock appears in the weight list at a default weight of 10%. Adjust the other weights to bring the total back to 100% before clicking Update Portfolio.

---

### Removing a Stock

Click the red **✕** button next to any stock in the Edit Portfolio panel. This sets its weight to zero. The stock will be permanently removed the next time you click **Update Portfolio**.

After removing a stock, redistribute its weight among the remaining stocks before submitting.

---

### Resetting to Default

Click **Reset to Default** in the Edit Portfolio panel to restore the portfolio to its original composition. The dashboard will refresh automatically.

---

## Project Structure

```
/portfolio-risk-dashboard
    /app
        /api
            main.py                 # FastAPI application entry point
            routes.py               # API route definitions and data models
        /cache                      # Auto-generated stock data cache (JSON)
        __init__.py                 # Empty file to allow for imports
        data_collector.py           # yfinance data fetching and caching
        influx_writer.py            # InfluxDB write operations
        metadata_storage.py         # Portfolio state storage
        portfolio_processor.py      # Portfolio aggregation
        risk_calculations.py        # Beta, alpha, Sharpe, and return calculations
    /data
        *-port.csv                  # Portfolio CSV files
    /docker
        docker-compose.yml          # InfluxDB and Grafana configuration
        .env                        # Environment variables (filled during setup)
    /grafana
        dashboard.json              # Grafana dashboard metadata (import during setup)
    load_dashboard.py               # Startup data loader script
    README.md                       # Current file
    requirements.txt                # Python dependencies
    run_api.py                      # API launcher
```

---

## Acknowledgements

Developed as a senior project at Oral Roberts University.

Special thanks to **Dr. Stephen Wheat** for technical guidance and **Dr. Ann-Marie Constable** for financial expertise in validating the risk metric calculations.
