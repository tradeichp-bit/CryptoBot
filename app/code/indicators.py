# Import necessary libraries
import csv
from app.code.bitvavo import Bitvavo
import requests
import re
import time
import yaml

# Load secrets from secrets.yaml
with open('app/secrets/secrets.yaml', 'r') as file:
    secrets = yaml.safe_load(file)

# Replace hardcoded TAAPI_API_KEY with dynamic loading
TAAPI_API_KEY = secrets['TAAPI_API_KEY']

# Define the TAAPI.io API key and base URL for technical analysis indicators
TAAPI_BASE_URL = "https://api.taapi.io"
BITVAVO_API_URL = "https://api.bitvavo.com/v2/ticker/price"

# Replace hardcoded APIKEY and APISECRET with dynamic loading
bitvavo = Bitvavo({
    'APIKEY': secrets['APIKEY'],
    'APISECRET': secrets['APISECRET'],
    'RESTURL': 'https://api.bitvavo.com/v2',
    'WSURL': 'wss://ws.bitvavo.com/v2/',
})

def get_tickers_with_more_than_one_year():
    try:
        # Get all available markets
        response = requests.get(BITVAVO_API_URL)
        response.raise_for_status()
        markets = response.json()
        valid_tickers = []
        for market in markets:
            market= market['market']
            candles = bitvavo.candles(market, '1M')
            if len(candles) > 24:
               valid_tickers.append(re.sub(r'-.*$', '/USDT', market))
        return valid_tickers
    except Exception as e:
        print(f"Error getting tickers: {e}")
        return []

def save_tickers_to_file(tickers, filename='app/tickers.txt'):
    try:
        with open(filename, 'w') as file:
            for ticker in tickers:
                file.write(f"{ticker}\n")
        print(f"Tickers saved to {filename}")
    except Exception as e:
        print(f"Error saving tickers to file: {e}")

# Function to fetch all available tickers from the Bitvavo API
def create_tickers_file():
    tickers = get_tickers_with_more_than_one_year()
    save_tickers_to_file(tickers)

def get_tickers():
    try:
        response = requests.get(BITVAVO_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tickers: {e}")
        return None

# Generic function to fetch indicators from TAAPI.io
def fetch_indicator(ticker, indicator):
    try:
        url = f"{TAAPI_BASE_URL}/{indicator}"
        params = {
            "secret": TAAPI_API_KEY,
            "exchange": "gateio",
            "symbol": ticker,
            "interval": "1h"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {indicator} for {ticker}: {e}")
        return None

# Specific indicator functions
def get_rsi(ticker):
    data = fetch_indicator(ticker, "rsi")
    return data.get("value") if data else None

def get_stoch(ticker):
    return fetch_indicator(ticker, "stoch")

def get_bollingerbands(ticker):
    return fetch_indicator(ticker, "bbands")

def get_macd(ticker):
    return fetch_indicator(ticker, "macd")

# Function to read tickers from a file
def read_tickers_from_file(file_path="app/tickers.txt"):
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print("Tickers file not found.")
        return []

# Function to generate CSV files for oversold and overbought tickers
def generate_csv():
    oversold = []
    overbought = []
    tickers = read_tickers_from_file()
    for ticker in tickers:
        rsi = get_rsi(ticker)
        stoch = get_stoch(ticker)
        macd = get_macd(ticker)
        bollinger = get_bollingerbands(ticker)
        time.sleep(5)  # Pause to avoid hitting API rate limits
        if bollinger:
            valueUpperBand = bollinger.get('valueUpperBand', 0)
            valueMiddleBand = bollinger.get('valueMiddleBand', 0)
            valueLowerBand = bollinger.get('valueLowerBand', 0)
        else:
            valueUpperBand = valueMiddleBand = valueLowerBand = 0
        if rsi is not None:
            data = [ticker, rsi, round(valueUpperBand, 6), round(valueMiddleBand, 6), round(valueLowerBand, 6), stoch, macd]
            if rsi < 30:
                oversold.append(data)
            elif rsi > 70:
                overbought.append(data)
    write_csv('app/csv/oversold.csv', oversold)
    write_csv('app/csv/overbought.csv', overbought)

# Function to write data to a CSV file
def write_csv(file_path, data):
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Ticker', 'RSI', 'valueUpperBand', 'valueMiddleBand', 'valueLowerBand', 'Stoch', 'MACD'])
        writer.writerows(data)
    print(f"File '{file_path}' generated successfully.")