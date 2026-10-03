import requests
import sqlite3
import os
from datetime import datetime

URL_OFFICIAL = "https://open.er-api.com/v6/latest/USD"
URL_FREE = "https://call2.tgju.org/ajax.json"
DB_NAME = "dollar_prices.db"

def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            official INTEGER,
            free_market INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_official_price():
    try:
        response = requests.get(URL_OFFICIAL, timeout=10)
        response.raise_for_status()
        data = response.json()
        irr_price = data["rates"].get("IRR")
        if irr_price is None:
            return None
        return int(irr_price)
    except Exception as e:
        print(f"Official Error: {e}")
        return None

def get_free_market_price():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(URL_FREE, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        dollar_data = data.get("current", {}).get("price_dollar_rl")
        if not dollar_data:
            return None
        price_str = dollar_data.get("p", "0").replace(",", "")
        return int(price_str)
    except Exception as e:
        print(f"Free Market Error: {e}")
        return None

def save_to_db(official, free):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("""
        INSERT INTO prices (date, time, official, free_market, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        now.strftime("%Y-%m-%d"),
        now.strftime("%H:%M:%S"),
        official,
        free,
        now.strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def main():
    init_database()
    print("Fetching dollar prices...")
    official = get_official_price()
    free = get_free_market_price()
    if official or free:
        save_to_db(official, free)
        if official:
            print(f"Official: {official:,} IRR")
        if free:
            print(f"Free Market: {free:,} IRR")
        print(f"Saved to database: {DB_NAME}")
    else:
        print("Operation failed.")

if __name__ == "__main__":
    main()
