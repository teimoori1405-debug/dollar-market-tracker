import sqlite3

DB_NAME = "dollar_prices.db"

def run(title, query):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print('=' * 50)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query)
    for row in cursor.fetchall():
        print(row)
    conn.close()

# Challenge 1: which day had the highest free market price
run(
    "Best day for free market",
    """SELECT date, MAX(free_market)
       FROM prices
       GROUP BY date
       ORDER BY MAX(free_market) DESC
       LIMIT 1"""
)

# Challenge 2: gap percentage between official and free
run(
    "Gap percent",
    """SELECT
         date,
         free_market,
         official,
         ROUND((free_market - official) * 100.0 / official, 2) AS gap_pct
       FROM prices
       ORDER BY id DESC
       LIMIT 1"""
)

# Challenge 3: today's records only
run(
    "Today's records",
    """SELECT id, time, official, free_market
       FROM prices
       WHERE date = '2026-10-02'
       ORDER BY id DESC"""
)

# Challenge 4: records where free > 2,500,000
run(
    "Free market above 2.5M",
    """SELECT id, date, time, free_market
       FROM prices
       WHERE free_market > 2500000
       ORDER BY id DESC"""
)
