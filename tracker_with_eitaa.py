import os
import requests
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

URL_OFFICIAL = "https://open.er-api.com/v6/latest/USD"
URL_FREE = "https://call2.tgju.org/ajax.json"
DB_NAME = "/data/data/com.termux/files/home/projects/dollar-db/dollar_prices.db"

EITAA_TOKEN = os.getenv("EITAA_TOKEN")
EITAA_CHAT_ID = os.getenv("EITAA_CHAT_ID")

def get_official_price():
    try:
        r = requests.get(URL_OFFICIAL, timeout=10)
        irr = r.json()["rates"].get("IRR")
        return int(irr) if irr else None
    except Exception as e:
        print(f"Official Error: {e}")
        return None

def get_free_market_price():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(URL_FREE, headers=headers, timeout=10)
        dollar = r.json().get("current", {}).get("price_dollar_rl")
        if not dollar:
            return None
        return int(dollar.get("p", "0").replace(",", ""))
    except Exception as e:
        print(f"Free Market Error: {e}")
        return None

def get_last_price():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT free_market FROM prices ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def save_to_db(official, free):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, time TEXT NOT NULL,
            official INTEGER, free_market INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    now = datetime.now()
    cursor.execute("""
        INSERT INTO prices (date, time, official, free_market, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
          official, free, now.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def send_to_eitaa(text):
    url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
    data = {"chat_id": EITAA_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=data, timeout=10)
        result = r.json()
        if result.get("ok"):
            print("Alert sent to Eitaa!")
        else:
            print(f"Eitaa Error: {result}")
    except Exception as e:
        print(f"Eitaa Error: {e}")

def main():
    print("Fetching dollar prices...")
    official = get_official_price()
    free = get_free_market_price()

    if not (official or free):
        print("Failed to fetch prices.")
        return

    prev = get_last_price()
    save_to_db(official, free)

    if official:
        print(f"Official: {official:,} IRR")
    if free:
        print(f"Free Market: {free:,} IRR")

    if free and prev != free:
        diff = free - prev if prev else 0
        diff_str = f"+{diff:,}" if diff > 0 else f"{diff:,}"
        msg = (
            f"قیمت دلار به‌روز شد\n"
            f"بازار آزاد: {free:,} ریال\n"
            f"رسمی: {official:,} ریال\n"
            f"تغییر: {diff_str} ریال\n"
            f"زمان: {datetime.now().strftime('%H:%M:%S')}"
        )
        send_to_eitaa(msg)
    else:
        print("Price unchanged. No alert sent.")

if __name__ == "__main__":
    main()
