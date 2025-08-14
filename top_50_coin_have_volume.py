import requests
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pytz

# ===== CONFIG =====
API_URL = "https://fapi.binance.com/fapi/v1/klines"
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT",
    "DOGEUSDT", "TRXUSDT", "MATICUSDT", "LTCUSDT", "DOTUSDT", "BCHUSDT",
    "AVAXUSDT", "UNIUSDT", "LINKUSDT", "ETCUSDT", "XLMUSDT", "APTUSDT",
    "FILUSDT", "SANDUSDT", "ATOMUSDT", "AAVEUSDT", "ICPUSDT", "NEARUSDT",
    "INJUSDT", "ARBUSDT", "OPUSDT", "DYDXUSDT", "RNDRUSDT", "PEPEUSDT"
]
INTERVAL = "15m"
LIMIT = 50
MAX_WORKERS = 10  # Giới hạn luồng tránh bị block
SLEEP_BETWEEN_REQUESTS = 0.05  # Giãn cách request
PERCENT_THRESHOLD = 0.1  # % phá đỉnh / phá đáy
TELEGRAM_TOKEN = "8226246719:AAHXDggFiFYpsgcq1vwTAWv7Gsz1URP4KEU"
TELEGRAM_CHAT_ID = "-4706073326"

# ===== HÀM GỬI TELEGRAM =====
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Telegram Error: {e}")

# ===== HÀM LẤY 50 CÂY NẾN =====
def fetch_klines(symbol):
    try:
        params = {"symbol": symbol, "interval": INTERVAL, "limit": LIMIT}
        response = requests.get(API_URL, params=params, timeout=5)
        data = response.json()

        if isinstance(data, list) and len(data) >= LIMIT:
            closes = [float(k[4]) for k in data]
            highs = [float(k[2]) for k in data]
            lows = [float(k[3]) for k in data]

            last_close = closes[-1]
            prev_high = max(highs[:-1])
            prev_low = min(lows[:-1])

            if last_close >= prev_high * (1 + PERCENT_THRESHOLD / 100):
                send_telegram(f"{symbol} 📈 Phá đỉnh {PERCENT_THRESHOLD}% - Giá đóng: {last_close}")
            elif last_close <= prev_low * (1 - PERCENT_THRESHOLD / 100):
                send_telegram(f"{symbol} 📉 Phá đáy {PERCENT_THRESHOLD}% - Giá đóng: {last_close}")

        time.sleep(SLEEP_BETWEEN_REQUESTS)
    except Exception as e:
        print(f"Lỗi lấy dữ liệu {symbol}: {e}")

# ===== CHẠY VÔ HẠN =====
def run():
    tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")
    while True:
        now_vn = datetime.now(tz_vn)
        if now_vn.minute % 15 == 0 and now_vn.second == 0:
            print(f"==> Bắt đầu check lúc {now_vn.strftime('%H:%M:%S')}")

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                executor.map(fetch_klines, SYMBOLS)

            wait_seconds = 15 * 60 - (datetime.now(tz_vn).minute % 15) * 60 - datetime.now(tz_vn).second
            print(f"Ngủ {wait_seconds} giây...")
            time.sleep(wait_seconds)
        else:
            time.sleep(0.5)

if __name__ == "__main__":
    run()
