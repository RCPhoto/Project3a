import os
import pygal
import requests
import webbrowser
from datetime import datetime
from flask import Flask, render_template, url_for

# Flask app initialization
app = Flask(__name__)

# Set API KEY for Alpha Vantage
#Static folder will get the SVG which is then uploaded to the html page
API_KEY = "K5MNQEQQ1D7IYJ0M"
STATICFOLD = os.path.join(os.getcwd(), 'static')

# Retrieve stock data from Alpha Vantage function
def retrieve_stock_data(stock_symbol, time_function, beginning_date, ending_date):
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
        date_range_data = {date: values for date, values in time_series_data.items()
                           if beginning_date <= date <= ending_date}

        if not date_range_data:
            print(f"No data found between {beginning_date} and {ending_date}.")
            return None


        print(f"Retrieved {len(date_range_data)} records.")
        return date_range_data
    else:
        print(f"Failed to retrieve data. HTTP Code: {api_response.status_code}")
        return None

# Function which generates the chart and saves to the static folder 
def generate_chart(data, chart_type, stock_symbol):
    print(f"Generating {chart_type} chart for {stock_symbol}")
    chart = pygal.Bar(title=f"{stock_symbol} Stock Prices") if chart_type == "1" else pygal.Line(title=f"{stock_symbol} Stock Prices")
    dates = sorted(data.keys())
    closing_prices = [float(data[date]['4. close']) for date in dates]

    chart.x_labels = dates
    chart.add(stock_symbol, closing_prices)

    # This it the path for saving the chart (SVG) to the static folder
    chart_file = os.path.join(STATICFOLD, f"{stock_symbol}_stock_chart.svg")



    # Guarantee/confirm that the static folder exists
    if not os.path.exists(STATICFOLD):
        os.makedirs(STATICFOLD)
        print(f"Created static folder: {STATICFOLD}")

    print(f"Saving chart to {chart_file}")
    chart.render_to_file(chart_file)
    return chart_file

# Flask route connection to chart
@app.route('/')
def display_chart():
    global stock_symbol, time_function, beginning_date, ending_date, chart_type
    
    
    # Retrieve stock data and generate the chart
    print("Retrieving stock data for chart generation...")
    stock_data = retrieve_stock_data(stock_symbol, time_function, beginning_date, ending_date)
    if stock_data:
        chart_path = generate_chart(stock_data, chart_type, stock_symbol)
        chart_url = url_for('static', filename=os.path.basename(chart_path))
        print(f"Chart URL for HTML: {chart_url}")
        return render_template('graphing.html', chart_data=chart_url, stock_symbol=stock_symbol)
    else:
        return "No data available for the given stock symbol and date range."

if __name__ == "__main__":
    print("Stock Data Visualizer")
    print("-----------------------")

    # Collect input from the user before running Flask
    stock_symbol = input("Enter the stock symbol you are looking for: ").upper()


    # Ask for chart type
    print("\nChart Types\n-------------\n1. Bar\n2. Line")
    chart_type = input("Enter the chart type you want (1 for Bar, 2 for Line): ")

    while chart_type not in ["1", "2"]:
        print("Invalid chart type, please try again.")
        chart_type = input("Enter the chart type you want (1 for Bar, 2 for Line): ")

    # Ask for time series
    print("\nSelect the Time Series of the chart you want to Generate")
    print("----------------------------------------------------------")
    print("1. Daily\n2. Weekly\n3. Monthly")
    time_series_option = input("Enter time series option (1, 2, 3): ")

    time_series_map = {
        "1": "TIME_SERIES_DAILY",
        "2": "TIME_SERIES_WEEKLY",
        "3": "TIME_SERIES_MONTHLY"
    }



    while time_series_option not in time_series_map:
        print("Invalid time series option, please try again.")
        time_series_option = input("Enter time series option (1, 2, 3): ")

    time_function = time_series_map[time_series_option]

    # Ask for start date and end date
    beginning_date = input("Enter the start date (YYYY-MM-DD): ")
    while not datetime.strptime(beginning_date, "%Y-%m-%d"):
        print("Invalid date format, please try again.")
        beginning_date = input("Enter the start date (YYYY-MM-DD): ")

    ending_date = input("Enter the end date (YYYY-MM-DD): ")
    while not datetime.strptime(ending_date, "%Y-%m-%d") or datetime.strptime(ending_date, "%Y-%m-%d") < datetime.strptime(beginning_date, "%Y-%m-%d"):
        print("Invalid end date or end date is before start date, please try again.")
        ending_date = input("Enter the end date (YYYY-MM-DD): ")

    # SHowing flask is running
    print("Starting the Flask server...")
    app.run(debug=False)