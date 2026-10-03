import requests
import sqlite3
from datetime import datetime

URL_OFFICIAL = "https://open.er-api.com/v6/latest/USD"
URL_TGJU = "https://call2.tgju.org/ajax.json"

DB_NAME = "/data/data/com.termux/files/home/projects/dollar-db/market_prices.db"

EITAA_TOKEN = "bot528938:fec8ce01-07f5-4f9f-a0ae-7f37df0a9379"
EITAA_CHAT_ID = "11266119"

PERIOD = 24
NEAR_PCT = 1.0
ASSETS = ["dollar", "euro", "gold_gram", "coin_emami"]
NAMES = {
    "dollar": "دلار آزاد",
    "euro": "یورو",
    "gold_gram": "طلای 24 عیار",
    "coin_emami": "سکه امامی",
}

def init_database():
    conn = sqlite3.connect(DB_NAME)
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, time TEXT NOT NULL,
            official INTEGER, dollar INTEGER, euro INTEGER,
            gold_gram INTEGER, coin_emami INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            asset TEXT PRIMARY KEY, state TEXT DEFAULT 'normal'
        )
    """)
    conn.commit(); conn.close()

def get_tgju(key):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(URL_TGJU, headers=headers, timeout=10)
        item = r.json().get("current", {}).get(key)
        return int(item.get("p", "0").replace(",", "")) if item else None
    except Exception as e:
        print(f"TGJU Error ({key}): {e}"); return None

def get_official():
    try:
        r = requests.get(URL_OFFICIAL, timeout=10)
        irr = r.json()["rates"].get("IRR")
        return int(irr) if irr else None
    except Exception as e:
        print(f"Official Error: {e}"); return None

def get_history(asset, limit=PERIOD):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT {asset} FROM prices WHERE {asset} IS NOT NULL ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall(); conn.close()
    return [row[0] for row in rows]

def get_alert_state(asset):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT state FROM alerts WHERE asset=?", (asset,))
    row = cursor.fetchone(); conn.close()
    return row[0] if row else "normal"

def save_alert_state(asset, state):
    conn = sqlite3.connect(DB_NAME)
    conn.cursor().execute("""
        INSERT INTO alerts (asset, state) VALUES (?, ?)
        ON CONFLICT(asset) DO UPDATE SET state=excluded.state
    """, (asset, state))
    conn.commit(); conn.close()

def save_to_db(d):
    conn = sqlite3.connect(DB_NAME)
    now = datetime.now()
    conn.cursor().execute("""
        INSERT INTO prices (date, time, official, dollar, euro, gold_gram, coin_emami, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
          d["official"], d["dollar"], d["euro"], d["gold_gram"], d["coin_emami"],
          now.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); conn.close()

def send_to_eitaa(text):
    url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": EITAA_CHAT_ID, "text": text}, timeout=10)
        if r.json().get("ok"): print("Sent.")
        else: print(f"Eitaa Error: {r.json()}")
    except Exception as e:
        print(f"Eitaa Error: {e}")

def fmt(v):
    return f"{v:,}" if v is not None else "N/A"

def analyze(asset, current):
    history = get_history(asset)
    if len(history) < 5:
        return None

    support = min(history)
    resistance = max(history)
    sma = sum(history) / len(history)

    # اگر تغییرات خیلی کم است، تحلیل معنی ندارد
    if resistance == support:
        return {"support": support, "resistance": resistance, "sma": sma,
                "current": current, "signal": "flat"}

    if current >= resistance:
        signal = "breakout_up"
    elif current <= support:
        signal = "breakout_down"
    elif (resistance - current) / resistance * 100 <= NEAR_PCT:
        signal = "near_resistance"
    elif (current - support) / support * 100 <= NEAR_PCT:
        signal = "near_support"
    else:
        signal = "normal"

    return {"support": support, "resistance": resistance, "sma": sma,
            "current": current, "signal": signal}

def build_alert(asset, a, prev):
    if a["signal"] == prev or a["signal"] in ("normal", "flat"):
        return None
    name = NAMES[asset]; cur = a["current"]
    s = a["support"]; r = a["resistance"]; sma = a["sma"]

    if a["signal"] == "breakout_up":
        return f"🚀 شکست سقف: {name}\nقیمت: {fmt(cur)} ریال\nسقف قبلی: {fmt(r)} ریال\nمیانگین: {fmt(int(sma))} ریال"
    if a["signal"] == "breakout_down":
        return f"🔻 شکست کف: {name}\nقیمت: {fmt(cur)} ریال\nکف قبلی: {fmt(s)} ریال\nمیانگین: {fmt(int(sma))} ریال"
    if a["signal"] == "near_resistance":
        return f"⚠️ نزدیک سقف: {name}\nقیمت: {fmt(cur)} ریال\nسقف: {fmt(r)} ریال\nفاصله: {r-cur:,} ریال"
    if a["signal"] == "near_support":
        return f"⚠️ نزدیک کف: {name}\nقیمت: {fmt(cur)} ریال\nکف: {fmt(s)} ریال\nفاصله: {cur-s:,} ریال"
    return None

def main():
    init_database()
    print("Fetching market prices...")

    d = {
        "official": get_official(),
        "dollar": get_tgju("price_dollar_rl"),
        "euro": get_tgju("price_eur"),
        "gold_gram": get_tgju("geram24"),
        "coin_emami": get_tgju("sekee"),
    }
    for k, v in d.items(): print(f"{k}: {v}")

    save_to_db(d)

    report = [f"📊 تحلیل تکنیکال - {datetime.now().strftime('%H:%M')}", ""]
    alerts = []

    for asset in ASSETS:
        current = d.get(asset)
        if current is None: continue

        a = analyze(asset, current)
        if not a:
            report.append(f"{NAMES[asset]}: داده کافی نیست")
            continue

        s = a["support"]; r = a["resistance"]; sma = a["sma"]
        if r > s:
            pos = f"{(current - s) / (r - s) * 100:.0f}%"
        else:
            pos = "ثابت"

        report.append(
            f"{NAMES[asset]}\n"
            f"  فعلی: {fmt(current)}\n"
            f"  کف: {fmt(s)} | سقف: {fmt(r)}\n"
            f"  میانگین: {fmt(int(sma))}\n"
            f"  موقعیت: {pos}"
        )

        prev_state = get_alert_state(asset)
        msg = build_alert(asset, a, prev_state)
        if msg:
            alerts.append(msg)
            save_alert_state(asset, a["signal"])
        else:
            save_alert_state(asset, a["signal"])

    report.append("")
    report.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    send_to_eitaa("\n".join(report))
    for alert in alerts:
        print(f"ALERT: {alert}")
        send_to_eitaa(alert)
    if not alerts:
        print("No alerts.")

if __name__ == "__main__":
    main()
