import time
import random
import requests
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# TELEGRAM CONFIG
# ═══════════════════════════════════════════════════════════════
BOT_TOKEN = '8151103901:AAGGZNOwfRbTKbi1b2laaC4HnsE_wfExCgo'
CHAT_ID = '-1004435782162'
STICKER_WIN = 'CAACAgUAAx0EeI6HAAMj_Whw5TMU5ag4PMlFPyUEMO6SI1KeAAKjFwACZ5ZZVfPMDRsGmT4HNgQ'
STICKER_LOSS = 'CAACAgUAAxkBAAE3mCRocOLFJATgelUZIAb15Aa64nd_iAACdRIAAm9BwVam2dyLbNeO8zYE'

# ═══════════════════════════════════════════════════════════════
# ✅ API URLs — Multiple endpoints for redundancy
# ═══════════════════════════════════════════════════════════════
API_ENDPOINTS = [
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json?ts=",  # cache buster
]

CORS_PROXIES = [
    "https://corsproxy.io/?",
    "https://api.allorigins.win/raw?url=",
    "https://cors-anywhere.herokuapp.com/",
]

# ═══════════════════════════════════════════════════════════════
# ✅ GLOBAL HTTP HEADERS — Important for VPS
# ═══════════════════════════════════════════════════════════════
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://draw.ar-lottery01.com/',
    'Origin': 'https://draw.ar-lottery01.com',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
}

# ═══════════════════════════════════════════════════════════════
# TELEGRAM HELPERS
# ═══════════════════════════════════════════════════════════════
def send_text(msg):
    """Send text message to Telegram"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
        time.sleep(0.4)
    except Exception as e:
        print(f"❌ send_text: {e}")


def send_sticker(sticker_id):
    """Send sticker to Telegram"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendSticker",
            data={"chat_id": CHAT_ID, "sticker": sticker_id},
            timeout=10
        )
        time.sleep(0.4)
    except Exception as e:
        print(f"❌ send_sticker: {e}")


# ═══════════════════════════════════════════════════════════════
# ✅ API FETCH — Multi-endpoint + Proxy Fallback
# ═══════════════════════════════════════════════════════════════
def fetch_api_data():
    """
    Fetch WinGo API with multiple fallbacks:
    1. Direct call with full headers
    2. Direct call with cache-buster
    3. Each CORS proxy
    Returns parsed JSON or None
    """
    ts = int(time.time() * 1000)

    # ─── METHOD 1: Direct with cache buster ───
    for api in API_ENDPOINTS:
        try:
            url = api + str(ts) if api.endswith("=") else api
            res = requests.get(url, timeout=8, headers=HTTP_HEADERS)
            if res.status_code == 200:
                data = res.json()
                if data.get("data", {}).get("list"):
                    return data
        except Exception as e:
            print(f"❌ Direct API failed: {e}")

    # ─── METHOD 2: CORS Proxies ───
    base_url = API_ENDPOINTS[0]
    for proxy in CORS_PROXIES:
        try:
            if proxy.endswith("="):
                url = proxy + requests.utils.quote(base_url, safe='')
            else:
                url = proxy + base_url
            res = requests.get(url, timeout=10, headers=HTTP_HEADERS)
            if res.status_code == 200:
                data = res.json()
                if data.get("data", {}).get("list"):
                    print(f"✅ Proxy success: {proxy}")
                    return data
        except Exception as e:
            print(f"❌ Proxy failed: {proxy} → {e}")

    return None


# ═══════════════════════════════════════════════════════════════
# ✅ GET LATEST PERIOD
# ═══════════════════════════════════════════════════════════════
def get_latest_period():
    """Return latest closed issueNumber (string) or None"""
    data = fetch_api_data()
    if not data:
        return None
    results = data.get("data", {}).get("list", [])
    if not results:
        return None
    return str(results[0].get("issueNumber", ""))


# ═══════════════════════════════════════════════════════════════
# ✅ RANDOM PREDICTION (80% WIN BIAS)
# ═══════════════════════════════════════════════════════════════
def make_random_prediction():
    """
    Returns (predicted_type, predicted_number)
    - 80% chance: biased toward recent trend (winning)
    - 20% chance: contrarian
    """
    data = fetch_api_data()
    if not data:
        # Pure random fallback
        ptype = random.choice(["BIG", "SMALL"])
        pnum = random.randint(0, 9)
        return ptype, pnum

    results = data.get("data", {}).get("list", [])
    if not results:
        ptype = random.choice(["BIG", "SMALL"])
        pnum = random.randint(0, 9)
        return ptype, pnum

    # Analyze last 5
    last_nums = [int(r.get("number", 0)) for r in results[:5]]
    types = ["BIG" if n >= 5 else "SMALL" for n in last_nums]
    big_count = types.count("BIG")
    small_count = types.count("SMALL")

    # 80% follow trend, 20% contrarian
    if random.random() < 0.80:
        ptype = "BIG" if big_count >= small_count else "SMALL"
    else:
        ptype = "SMALL" if big_count >= small_count else "BIG"

    # Random number
    pnum = random.randint(0, 9)

    # Align number with type
    if ptype == "BIG" and pnum < 5:
        pnum = random.randint(5, 9)
    elif ptype == "SMALL" and pnum >= 5:
        pnum = random.randint(0, 4)

    return ptype, pnum


# ═══════════════════════════════════════════════════════════════
# ✅ CHECK RESULT FOR A PERIOD
# ═══════════════════════════════════════════════════════════════
def check_result(target_period, predicted_type, predicted_number, timeout_sec=75):
    """Check target period's result in API"""
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            data = fetch_api_data()
            if data:
                results = data.get("data", {}).get("list", [])
                for item in results:
                    if str(item.get("issueNumber")) == str(target_period):
                        actual = int(item["number"])
                        actual_type = "BIG" if actual >= 5 else "SMALL"
                        if actual == predicted_number or actual_type == predicted_type:
                            return "WIN", actual, actual_type
                        else:
                            return "LOSS", actual, actual_type
        except Exception as e:
            print(f"Result check error: {e}")
        time.sleep(3)
    return "NO_RESULT", None, None


# ═══════════════════════════════════════════════════════════════
# ✅ WAIT UNTIL XX:00
# ═══════════════════════════════════════════════════════════════
def wait_until_next_minute():
    now = datetime.now()
    sec = now.second
    if sec > 0:
        wait_time = 60 - sec
        print(f"⏳ Waiting {wait_time}s until XX:00...")
        time.sleep(wait_time + 0.5)


# ═══════════════════════════════════════════════════════════════
# ✅ SEND PREDICTION TO TELEGRAM
# ═══════════════════════════════════════════════════════════════
def send_prediction(period, ptype, pnumber, wins, losses):
    msg = (
        f"🎯 *NEW PREDICTION*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 *Period:* `{period}`\n"
        f"🎲 *Prediction:* `{pnumber}` ({ptype})\n"
        f"⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 *Score:* {wins}W / {losses}L\n"
        f"_Result @ next minute :00_"
    )
    send_text(msg)


# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN LOOP — NEVER STOPS
# ═══════════════════════════════════════════════════════════════
def main():
    total_wins = 0
    total_losses = 0
    last_predicted_period = None
    consecutive_api_fails = 0

    print("🤖 Deathmark Bot Started — Infinite Mode")
    send_text(
        "🤖 *Bot Started — WinGo 1M Clock Mode*\n"
        "♾️ Infinite · Never stops\n"
        "⏰ Prediction @ XX:00 · Result @ XX+1:00"
    )

    # Initial align
    wait_until_next_minute()

    while True:
        try:
            # ─── STEP A: Latest period → next = latest + 1 ───
            latest = get_latest_period()

            if not latest:
                consecutive_api_fails += 1
                wait = min(60, 20 * consecutive_api_fails)  # Adaptive backoff
                print(f"⚠️ API failed ({consecutive_api_fails}x), retry in {wait}s...")
                time.sleep(wait)
                continue

            # API working → reset fail counter
            consecutive_api_fails = 0

            try:
                next_period = str(int(latest) + 1)
            except Exception:
                time.sleep(20)
                continue

            # ─── STEP B: Skip duplicate ───
            if next_period == last_predicted_period:
                print(f"⚠️ Same period {next_period}, waiting 30s...")
                time.sleep(30)
                continue

            # ─── STEP C: Make prediction ───
            ptype, pnumber = make_random_prediction()
            print(f"\n{'=' * 55}")
            print(f"📊 Period: {next_period} | Prediction: {pnumber} ({ptype})")
            print(f"🏆 Score: {total_wins}W / {total_losses}L")

            # ─── STEP D: Send to Telegram ───
            send_prediction(next_period, ptype, pnumber, total_wins, total_losses)
            last_predicted_period = next_period

            # ─── STEP E: Wait until XX:00 ───
            wait_until_next_minute()

            # ─── STEP F: Check result ───
            print(f"🔍 Checking result for period {next_period}...")
            result, actual_num, actual_type = check_result(
                next_period, ptype, pnumber, timeout_sec=75
            )

            # ─── STEP G: Send result ───
            if result == "WIN":
                total_wins += 1
                send_sticker(STICKER_WIN)
                send_text(
                    f"✅ *WIN!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔢 Period: `{next_period}`\n"
                    f"🎯 Predicted: `{pnumber}` ({ptype})\n"
                    f"📊 Actual: `{actual_num}` ({actual_type})\n"
                    f"🏆 *Score:* {total_wins}W / {total_losses}L"
                )
                print(f"✅ WIN! ({total_wins}W / {total_losses}L)")

            elif result == "LOSS":
                total_losses += 1
                send_sticker(STICKER_LOSS)
                send_text(
                    f"❌ *LOSS*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔢 Period: `{next_period}`\n"
                    f"🎯 Predicted: `{pnumber}` ({ptype})\n"
                    f"📊 Actual: `{actual_num}` ({actual_type})\n"
                    f"🏆 *Score:* {total_wins}W / {total_losses}L"
                )
                print(f"❌ LOSS ({total_wins}W / {total_losses}L)")

            else:
                send_text(
                    f"⚠️ *Result Timeout*\n"
                    f"Period `{next_period}` result miss.\n"
                    f"Continuing..."
                )
                print("⚠️ No result")

            # ─── STEP H: Buffer ───
            time.sleep(3)

        except KeyboardInterrupt:
            send_text(
                f"🛑 *Bot stopped manually*\n"
                f"🏆 Final: {total_wins}W / {total_losses}L"
            )
            print(f"\n🛑 Stopped. Score: {total_wins}W / {total_losses}L")
            break

        except Exception as e:
            print(f"⚠️ Loop error: {e}")
            time.sleep(10)


# ═══════════════════════════════════════════════════════════════
# ENTRY
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
