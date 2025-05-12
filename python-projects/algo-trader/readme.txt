Nifty 50 Algo Trading Program
=============================

Overview
--------
This Python-based algorithmic trading bot is designed to automate intraday trading on Nifty 50 stocks using the Dhan trading API.
It securely connects to the Dhan platform via API credentials (Client ID and Token), monitors account status, executes predefined strategies,
and generates end-of-day trading reports.

Key Features
------------
✔ Connects to Dhan API using Client ID and API Token
✔ Validates and retrieves account information
✔ Fetches live holdings and open positions
✔ Executes predefined intraday strategies on Nifty 50 stocks
✔ Automatically places buy/sell orders
✔ Logs each trade and event
✔ Generates a summary report at the end of trading day

Workflow
--------
1. **API Authentication**
   - Reads your Dhan Client ID and API token from a secure config file or environment variable
   - Authenticates the session for order placement and data access

2. **Data Fetching**
   - Loads Nifty 50 symbols
   - Fetches current holdings and open positions
   - Retrieves live price data (LTP)

3. **Strategy Execution**
   - Applies custom technical or quantitative logic to each stock
   - Signals buy/sell actions based on real-time data
   - Places market or limit orders via Dhan API

4. **Trade Logging**
   - Each order response is logged with status, price, quantity, and time
   - Logs errors, rejected orders, or API timeouts

5. **End-of-Day Report**
   - Summarizes:
     - Total trades executed
     - Net P&L (if enabled)
     - Positions carried forward
     - Strategy performance metrics

Requirements
------------
- Python 3.7 or higher
- Dhan Developer API access
- `requests`, `pandas`, `datetime`, `json`, `time`, `logging`

Install dependencies using:
    pip3 install requests pandas

Usage
-----
1. Configure your API credentials in a secure config file or environment variable:
    Example (config.json):
    {
        "client_id": "YOUR_DHAN_CLIENT_ID",
        "access_token": "YOUR_DHAN_API_TOKEN"
    }

2. Run the trading bot from terminal:
    python3 nifty50_algo.py

3. Ensure the market is live (between 9:15 AM to 3:30 PM IST)

4. At the end of the day, a summary report will be saved in `/reports` folder (e.g., `EOD_Report_2025-05-12.csv`)

Security Tips
-------------
- Never hardcode or commit your API keys to GitHub
- Add `config.json` to your `.gitignore` file
- Use `.env` or a secure vault for key management in production

Disclaimer
----------
This project is intended for educational and research purposes only.
Trading in the stock market involves financial risk. Use at your own discretion.

Author
------
Ajay (your name or GitHub handle here)

License
-------
MIT License (or any open license of your choice)

