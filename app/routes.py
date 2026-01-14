import os
from flask import Flask, render_template, request
import pandas as pd
from app import app
from app.code.indicators import get_rsi, get_stoch, get_bollingerbands, get_macd, generate_csv, create_tickers_file
from apscheduler.schedulers.background import BackgroundScheduler

# Define the folder where CSV files will be stored
CSV_FOLDER = os.path.join(os.getcwd(), 'app/csv')

# Initialize the background scheduler
scheduler = BackgroundScheduler()

# Schedule the generate_csv function to run every 5 minutes
scheduler.add_job(
    func=generate_csv,
    trigger="interval",
    minutes=5
)

# Schedule the create_tickers_file function to run every 2 days
scheduler.add_job(
    func=create_tickers_file,
    trigger="interval",
    minutes=2880
)

# Start the scheduler
scheduler.start()

@app.route("/", methods=["GET", "POST"])
def index():
    analysis = None
    ticker = None

    if request.method == "POST":
        ticker = request.form.get("ticker").strip()
        try:
            rsi = get_rsi(ticker)
            stoch = get_stoch(ticker)
            bb = get_bollingerbands(ticker)
            macd = get_macd(ticker)

            analysis = {
                "RSI": rsi,
                "Stochastic": stoch,
                "Bollinger Bands": bb,
                "MACD": macd
            }
        except Exception as e:
            analysis = {"error": f"Failed to fetch data for {ticker}: {e}"}

    # List all CSV files in the CSV folder
    csv_files = [f for f in os.listdir(CSV_FOLDER) if f.endswith('.csv')]
    return render_template("index.html", ticker=ticker, analysis=analysis, csv_files=csv_files)

@app.route("/csv/<filename>")
def show_csv(filename):
    file_path = os.path.join(CSV_FOLDER, filename)
    if os.path.exists(file_path):
        # Read the CSV file and extract headers and rows
        data = pd.read_csv(file_path)
        headers = data.columns.tolist()
        rows = data.values.tolist()
        return render_template('csv_view.html', filename=filename, headers=headers, rows=rows)
    else:
        return "File not found", 404

# Helper function to read tickers from the file
def read_tickers_from_file():
    try:
        with open("tickers.txt", "r") as file:
            tickers = [line.strip() for line in file.readlines()]
        return tickers
    except FileNotFoundError:
        print("Tickers file not found.")
        return []