# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 13:36:50 2024

@author: Robby
"""
import os
from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import requests
from datetime import datetime

API_KEY = "K5MNQEQQ1D7IYJ0M"
STATICFOLD = os.path.join(os.getcwd(), 'static')

app = Flask(__name__)

def get_stock_symbols():
    df = pd.read_csv("stocks.csv")
    symbols = df["Symbol"].tolist()
    return symbols

def get_stock_data(stock_symbol, time_function, beginning_date, ending_date):
    try:
        print(f"Retrieving data for {stock_symbol} from {beginning_date} to {ending_date}")
        start_date_input = datetime.strptime(beginning_date, "%Y-%m-%d")
        end_date_input = datetime.strptime(ending_date, "%Y-%m-%d")

        if end_date_input < start_date_input:
            raise ValueError("Start date must be before end date.")
    except ValueError as e:
        print(f"Error in date input: {e}")
        return None

    # Build URL for Alpha Vantage API
    url = (f"https://www.alphavantage.co/query?function={time_function}"
           f"&symbol={stock_symbol}&apikey={API_KEY}&outputsize=full&datatype=json")
    print(f"API URL: {url}")
    api_response = requests.get(url)

    if api_response.status_code == 200:
        stock_data = api_response.json()
        time_type = {
            "TIME_SERIES_DAILY": "Time Series (Daily)",
            "TIME_SERIES_WEEKLY": "Weekly Time Series",
            "TIME_SERIES_MONTHLY": "Monthly Time Series"
        }.get(time_function)

        if not time_type:
            print("Time function not supported.")
            return None

        time_series_data = stock_data.get(time_type, {})

        # Convert dates to datetime objects for comparison
        date_range_data = {
            datetime.strptime(date, "%Y-%m-%d"): values
            for date, values in time_series_data.items()
            if start_date_input <= datetime.strptime(date, "%Y-%m-%d") <= end_date_input
        }

        if not date_range_data:
            return None

        return date_range_data
    else:
        print(f"Failed to retrieve data. HTTP Code: {api_response.status_code}")
        return None

def create_chart(data, chart_type):
    if not data:
        return None

    df = pd.DataFrame(data).T 
    df.index = pd.to_datetime(df.index) 

    # Extract closing prices
    closing_prices = df['4. close'].astype(float)

    if chart_type == 'line':
        plt.figure(figsize=(10, 5))
        plt.plot(closing_prices)
        plt.title('Stock Closing Prices')
        plt.xlabel('Date')
        plt.ylabel('Price')
    elif chart_type == 'bar':
        plt.figure(figsize=(10, 5))
        plt.bar(closing_prices.index, closing_prices.values)
        plt.title('Stock Closing Prices')
        plt.xlabel('Date')
        plt.ylabel('Price')
    else:
        return None  # Invalid chart type

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return plot_url

@app.route("/", 
 methods=["GET", "POST"])
def index():
    stock_symbols = get_stock_symbols()
    chart_url = None
    if request.method == "POST":
        symbol = request.form["symbol"]
        chart_type = request.form["chart_type"]
        time_function = request.form["time_function"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        # Fetch and process data
        data = get_stock_data(symbol, time_function, start_date, end_date)

        # Generate chart
        chart_url = create_chart(data, chart_type)
    return render_template("index.html", symbols=stock_symbols, chart_url=chart_url)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)