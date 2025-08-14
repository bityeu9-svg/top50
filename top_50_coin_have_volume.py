import requests
import time
from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta

BINANCE_FAPI_KLINES = "https://fapi.binance.com/fapi/v1/klines"
INTERVAL = "15m"
BREAKOUT_THRESHOLD = 0.003   # 0.3% breakout
STOP_LOSS_PERCENT  = 0.005   # 0.5% SL
TAKE_PROFIT_PERCENT= 0.01    # 1% TP

# Danh sách 30 cặp coin muốn theo dõi
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "TRXUSDT", "MATICUSDT", "LTCUSDT",
    "DOTUSDT", "SHIBUSDT", "LINKUSDT", "BCHUSDT", "AVAXUSDT",
    "XLMUSDT", "UNIUSDT", "ATOMUSDT", "ETCUSDT", "FILUSDT",
    "ICPUSDT", "APTUSDT", "NEARUSDT", "VETUSDT", "ARBUSDT",
    "GALAUSDT", "OPUSDT", "AAVEUSDT", "SANDUSDT", "EGLDUSDT"
]

# Telegram config
TELEGRAM_BOT_TOKEN = "8226246719:AAHXDggFiFYpsgcq1vwTAWv7Gsz1URP4KEU"
TELEGRAM_CHAT_ID = "-4706073326"

# Múi giờ Việt Nam
VN_TZ = timezone(timedelta(hours=7))

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Lỗi gửi Telegram:", e)

def get_last_50_closed_klines(symbol: str, interval: str):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 51
    }
    r = requests.get(BINANCE_FAPI_KLINES, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data[:-1]  # bỏ nến đang chạy

def analyze_breakout(klines):
    last = klines[-1]
    prev49 = klines[:-1]

    last_high = float(last[2])
    last_low = float(last[3])
    last_close = float(last[4])

    prev_max_high = max(float(k[2]) for k in prev49)
    prev_min_low  = min(float(k[3]) for k in prev49)

    broke_high = last_high > prev_max_high * (1 + BREAKOUT_THRESHOLD)
    broke_low  = last_low  < prev_min_low  * (1 - BREAKOUT_THRESHOLD)

    close_time_ms = int(last[6])
    close_time = datetime.fromtimestamp(close_time_ms / 1000, tz=VN_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")

    return {
        "close_time": close_time,
        "last_high": last_high,
        "last_low": last_low,
        "last_close": last_close,
        "prev_49_max_high": prev_max_high,
        "prev_49_min_low": prev_min_low,
        "break_high": broke_high,
        "break_low": broke_low
    }

if __name__ == "__main__":
    print("🟢 Bot đang chạy...")
    send_telegram_message("Start server 50 coin")
    while True:
                try:
                    now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
                    if now_utc.minute % 60 == 0 and now_utc.second < 5:
                        for symbol in SYMBOLS:
                            kl = get_last_50_closed_klines(symbol, INTERVAL)
                            if len(kl) < 50:
                                print(f"{symbol}: Không đủ dữ liệu.")
                                continue

                            res = analyze_breakout(kl)

                            print(f"[{symbol}] {res['close_time']}")
                            print(f"  Last High: {res['last_high']:.8f} | Prev49 Max High: {res['prev_49_max_high']:.8f}")
                            print(f"  Last Low: {res['last_low']:.8f}  | Prev49 Min Low: {res['prev_49_min_low']:.8f}")

                            if res["break_high"]:
                                entry = res['last_close']
                                sl = entry * (1 + STOP_LOSS_PERCENT)  # SL
                                tp = entry * (1 - TAKE_PROFIT_PERCENT)  # TP
                                msg = (
                                    f"🚀 <b>{symbol}</b> phá ĐỈNH {res['last_high']:.8f} (+0.1%)\n"
                                    f"⏰ {res['close_time']}\n"
                                    f"📈 <b>Đề xuất (Kịch bản B)</b>\n"
                                    f"Entry: {entry:.8f}\n"
                                    f"SL: {sl:.8f}\n"
                                    f"TP: {tp:.8f}"
                                )
                                send_telegram_message(msg)

                            if res["break_low"]:
                                entry = res['last_close']
                                sl = entry * 1.005  # SL 0.5% trên entry
                                tp = entry * 0.99   # TP 1% dưới entry
                                msg = (
                                    f"📉 <b>{symbol}</b> phá ĐÁY {res['last_low']:.8f} (-0.1%)\n"
                                    f"⏰ {res['close_time']}\n"
                                    f"📉 <b>Đề xuất (Kịch bản B)</b>\n"
                                    f"Entry: {entry:.8f}\n"
                                    f"SL: {sl:.8f}\n"
                                    f"TP: {tp:.8f}"
                                )
                                send_telegram_message(msg)
                        time.sleep(9000 - now_utc.second % 60)  # Đợi hết 15 phút tránh trùng    
                    else:
                        time.sleep(1)
                except Exception as e:
                    print("Lỗi vòng lặp chính:", e)
                    send_telegram_message(e)
