import sqlite3

DB_NAME = "dollar_prices.db"

def run_query(title, query):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print('=' * 50)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    if not rows:
        print("No data.")
    else:
        for row in rows:
            print(row)
    conn.close()

run_query("All records", "SELECT * FROM prices ORDER BY id DESC LIMIT 10")

run_query("Total records", "SELECT COUNT(*) FROM prices")

run_query(
    "Average prices",
    "SELECT AVG(official), AVG(free_market) FROM prices"
)

run_query(
    "Min / Max",
    "SELECT MIN(free_market), MAX(free_market) FROM prices"
)

run_query(
    "Latest price",
    "SELECT date, time, official, free_market FROM prices ORDER BY id DESC LIMIT 1"
)

run_query(
    "Daily average",
    """SELECT date, AVG(official), AVG(free_market)
       FROM prices
       GROUP BY date
       ORDER BY date DESC"""
)
