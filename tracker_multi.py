import requests
import sqlite3
from datetime import datetime

URL_OFFICIAL = "https://open.er-api.com/v6/latest/USD"
URL_TGJU = "https://call2.tgju.org/ajax.json"

DB_NAME = "/data/data/com.termux/files/home/projects/dollar-db/market_prices.db"

EITAA_TOKEN = "bot528938:fec8ce01-07f5-4f9f-a0ae-7f37df0a9379"
EITAA_CHAT_ID = "11266119"

def init_database():
    conn = sqlite3.connect(DB_NAME)
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            official INTEGER,
            dollar INTEGER,
            euro INTEGER,
            gold_gram INTEGER,
            coin_emami INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_tgju(key):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(URL_TGJU, headers=headers, timeout=10)
        data = r.json()
        item = data.get("current", {}).get(key)
        if not item:
            return None
        return int(item.get("p", "0").replace(",", ""))
    except Exception as e:
        print(f"TGJU Error ({key}): {e}")
        return None

def get_official():
    try:
        r = requests.get(URL_OFFICIAL, timeout=10)
        irr = r.json()["rates"].get("IRR")
        return int(irr) if irr else None
    except Exception as e:
        print(f"Official Error: {e}")
        return None

def get_previous():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dollar, euro, gold_gram, coin_emami
        FROM prices ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {}
    return {
        "dollar": row[0],
        "euro": row[1],
        "gold_gram": row[2],
        "coin_emami": row[3],
    }

def save_to_db(d):
    conn = sqlite3.connect(DB_NAME)
    now = datetime.now()
    conn.cursor().execute("""
        INSERT INTO prices
        (date, time, official, dollar, euro, gold_gram, coin_emami, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
        d["official"], d["dollar"], d["euro"], d["gold_gram"], d["coin_emami"],
        now.strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def send_to_eitaa(text):
    url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": EITAA_CHAT_ID, "text": text}, timeout=10)
        if r.json().get("ok"):
            print("Report sent to Eitaa!")
        else:
            print(f"Eitaa Error: {r.json()}")
    except Exception as e:
        print(f"Eitaa Error: {e}")

def fmt_with_change(current, previous):
    if current is None:
        return "N/A"
    text = f"{current:,}"
    if previous and previous != current:
        diff = current - previous
        arrow = "▲" if diff > 0 else "▼"
        text += f"  {arrow} {abs(diff):,}"
    return text

def main():
    init_database()
    print("Fetching market prices...")

    prev = get_previous()

    d = {
        "official": get_official(),
        "dollar": get_tgju("price_dollar_rl"),
        "euro": get_tgju("price_eur"),
        "gold_gram": get_tgju("geram24"),
        "coin_emami": get_tgju("sekee"),
    }

    for k, v in d.items():
        print(f"{k}: {v}")
    print(f"previous: {prev}")

    msg = (
        f"گزارش بازار - {datetime.now().strftime('%H:%M')}\n"
        f"\n"
        f"دلار آزاد: {fmt_with_change(d['dollar'], prev.get('dollar'))} ریال\n"
        f"یورو: {fmt_with_change(d['euro'], prev.get('euro'))} ریال\n"
        f"طلای 24 عیار: {fmt_with_change(d['gold_gram'], prev.get('gold_gram'))} ریال\n"
        f"سکه امامی: {fmt_with_change(d['coin_emami'], prev.get('coin_emami'))} ریال\n"
        f"\n"
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    save_to_db(d)
    send_to_eitaa(msg)

if __name__ == "__main__":
    main()
