import sqlite3
import io
import base64
from datetime import datetime
from flask import Flask, render_template_string
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import jdatetime

DB_NAME = "/data/data/com.termux/files/home/projects/dollar-db/market_prices.db"

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>داشبورد بازار</title>
<style>
  body { font-family: Tahoma, sans-serif; background: #1a1a2e; color: #eee;
         margin: 0; padding: 20px; }
  h1 { color: #f0a500; text-align: center; }
  .toolbar { text-align: center; margin: 10px 0 20px 0; }
  .toolbar a { background: #f0a500; color: #1a1a2e; text-decoration: none;
               padding: 10px 20px; border-radius: 6px; font-weight: bold;
               display: inline-block; }
  .card { background: #16213e; border-radius: 12px; padding: 15px;
          margin: 15px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.4); }
  .card h2 { color: #f0a500; margin: 0 0 10px 0; font-size: 18px; }
  .stats { display: grid; grid-template-columns: repeat(2, 1fr);
           gap: 8px; margin-bottom: 10px; font-size: 14px; }
  .stat { background: #0f3460; padding: 8px; border-radius: 6px;
          display: flex; justify-content: space-between; }
  .stat b { color: #16c79a; }
  .up { color: #16c79a !important; }
  .down { color: #e94560 !important; }
  img { width: 100%; border-radius: 8px; }
  table { width: 100%; border-collapse: collapse; margin-top: 10px;
          font-size: 12px; }
  th, td { padding: 5px; text-align: center; border-bottom: 1px solid #333; }
  th { color: #f0a500; }
  .footer { text-align: center; color: #888; font-size: 12px;
            margin-top: 20px; }
</style>
</head>
<body>
  <h1>📊 داشبورد بازار</h1>
  <div class="toolbar">
    <a href="/">🔄 به‌روزرسانی</a>
  </div>
  {% for asset in assets %}
  <div class="card">
    <h2>{{ asset.name }}</h2>
    <div class="stats">
      <div class="stat">
        <span>فعلی:</span>
        <b class="{{ asset.trend }}">{{ "{:,}".format(asset.current) }}</b>
      </div>
      <div class="stat">
        <span>تغییر:</span>
        <b class="{{ asset.trend }}">{{ asset.diff_str }}</b>
      </div>
      <div class="stat">
        <span>میانگین:</span>
        <b>{{ "{:,}".format(asset.sma) }}</b>
      </div>
      <div class="stat">
        <span>موقعیت:</span>
        <b>{{ asset.position }}</b>
      </div>
      <div class="stat">
        <span>کف:</span>
        <b>{{ "{:,}".format(asset.support) }}</b>
      </div>
      <div class="stat">
        <span>سقف:</span>
        <b>{{ "{:,}".format(asset.resistance) }}</b>
      </div>
    </div>
    <img src="data:image/png;base64,{{ asset.chart }}" alt="chart">
    <table>
      <tr>
        <th>تاریخ</th>
        <th>ساعت</th>
        <th>قیمت</th>
        <th>تغییر</th>
      </tr>
      {% for row in asset.history %}
      <tr>
        <td>{{ row.date_jalali }}</td>
        <td>{{ row.time }}</td>
        <td>{{ "{:,}".format(row.value) }}</td>
        <td class="{{ row.trend }}">{{ row.diff_str }}</td>
      </tr>
      {% endfor %}
    </table>
  </div>
  {% endfor %}
  <div class="footer">آخرین به‌روزرسانی: {{ updated }}</div>
</body>
</html>
"""

NAMES = {
    "dollar": "💵 دلار آزاد",
    "euro": "💶 یورو",
    "gold_gram": "🥇 طلای 24 عیار",
    "coin_emami": "🪙 سکه امامی",
}

CHART_LABELS = {
    "price": "قیمت",
    "support": "کف",
    "resistance": "سقف",
    "sma": "میانگین",
}

def to_jalali_str(gregorian_str):
    try:
        g = datetime.strptime(gregorian_str, "%Y-%m-%d")
        j = jdatetime.date.fromgregorian(date=g)
        return j.strftime("%Y/%m/%d")
    except Exception:
        return gregorian_str

def get_history(asset, limit=48):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT date, time, created_at, {asset} FROM prices
        WHERE {asset} IS NOT NULL
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return list(reversed(rows))

def make_chart(history):
    # Use Gregorian datetime for plotting (matplotlib compatible)
    times = [datetime.strptime(r[2], "%Y-%m-%d %H:%M:%S") for r in history]
    values = [r[3] for r in history]

    support = min(values)
    resistance = max(values)
    sma = sum(values) / len(values)

    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor='#16213e')
    ax.set_facecolor('#0f3460')

    ax.plot(times, values, color='#f0a500', linewidth=2,
            label=CHART_LABELS["price"])
    ax.axhline(support, color='#16c79a', linestyle='--',
               linewidth=1, label=CHART_LABELS["support"])
    ax.axhline(resistance, color='#e94560', linestyle='--',
               linewidth=1, label=CHART_LABELS["resistance"])
    ax.axhline(sma, color='#a5a5a5', linestyle=':',
               linewidth=1, label=CHART_LABELS["sma"])

    # Format x-axis ticks as Jalali
    def jalali_formatter(x, pos=None):
        g = mdates.num2date(x).replace(tzinfo=None)
        j = jdatetime.datetime.fromgregorian(datetime=g)
        return j.strftime("%m/%d %H:%M")

    ax.xaxis.set_major_formatter(plt.FuncFormatter(jalali_formatter))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())

    ax.tick_params(colors='#ccc', labelsize=7)
    for spine in ax.spines.values():
        spine.set_color('#444')
    ax.legend(facecolor='#16213e', edgecolor='#444',
              labelcolor='#ccc', fontsize=8, loc='best')
    ax.grid(True, alpha=0.2)

    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=80, facecolor='#16213e')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def trend_class(diff):
    if diff > 0:
        return "up"
    elif diff < 0:
        return "down"
    return ""

def diff_string(diff):
    if diff > 0:
        return f"▲ +{diff:,}"
    elif diff < 0:
        return f"▼ {diff:,}"
    return "۰"

@app.route('/')
def index():
    assets = []
    for key, name in NAMES.items():
        history = get_history(key)
        if len(history) < 2:
            continue

        values = [r[3] for r in history]
        current = values[-1]
        prev = values[-2]
        diff = current - prev

        support = min(values)
        resistance = max(values)
        sma = int(sum(values) / len(values))

        if resistance > support:
            pos_val = (current - support) / (resistance - support) * 100
            position = f"{pos_val:.0f}%"
        else:
            position = "ثابت"

        hist_rows = []
        for i in range(len(history) - 1, max(len(history) - 11, -1), -1):
            h = history[i]
            d = 0
            if i > 0:
                d = h[3] - history[i - 1][3]
            hist_rows.append({
                "date_jalali": to_jalali_str(h[0]),
                "time": h[1],
                "value": h[3],
                "diff_str": diff_string(d),
                "trend": trend_class(d),
            })

        assets.append({
            "name": name,
            "current": current,
            "diff_str": diff_string(diff),
            "trend": trend_class(diff),
            "support": support,
            "resistance": resistance,
            "sma": sma,
            "position": position,
            "chart": make_chart(history),
            "history": hist_rows,
        })

    now_j = jdatetime.datetime.now()
    updated = now_j.strftime("%Y/%m/%d - %H:%M:%S")

    return render_template_string(
        HTML,
        assets=assets,
        updated=updated
    )

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False)
