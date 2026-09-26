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
# ✅ WinGo Direct API
# ═══════════════════════════════════════════════════════════════
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

CORS_PROXIES = [
    "https://corsproxy.io/?",
    "https://api.allorigins.win/raw?url=",
]


# ═══════════════════════════════════════════════════════════════
# TELEGRAM HELPERS
# ═══════════════════════════════════════════════════════════════
def send_text(msg):
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
# ✅ API FETCH WITH PROXY FALLBACK
# ═══════════════════════════════════════════════════════════════
def fetch_api_data():
    # Try direct
    try:
        res = requests.get(
            API_1M,
            timeout=8,
            headers={'Cache-Control': 'no-cache', 'User-Agent': 'Mozilla/5.0'}
        )
        if res.status_code == 200:
            data = res.json()
            if data.get("data", {}).get("list"):
                return data
    except Exception:
        pass

    # Try proxies
    for proxy in CORS_PROXIES:
        try:
            if proxy.endswith("="):
                url = proxy + requests.utils.quote(API_1M, safe='')
            else:
                url = proxy + API_1M
            res = requests.get(
                url,
                timeout=8,
                headers={'Cache-Control': 'no-cache', 'User-Agent': 'Mozilla/5.0'}
            )
            if res.status_code == 200:
                data = res.json()
                if data.get("data", {}).get("list"):
                    return data
        except Exception:
            pass

    return None


# ═══════════════════════════════════════════════════════════════
# ✅ GET LATEST PERIOD FROM API
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
    - 20% chance: contrarian (worst)
    Random number generated for display
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

    # Analyze last 5 for bias
    last_nums = [int(r.get("number", 0)) for r in results[:5]]
    types = ["BIG" if n >= 5 else "SMALL" for n in last_nums]
    big_count = types.count("BIG")
    small_count = types.count("SMALL")

    # 80% follow dominant trend (winning bias)
    if random.random() < 0.80:
        if big_count >= small_count:
            ptype = "BIG"
        else:
            ptype = "SMALL"
    else:
        # 20% contrarian
        if big_count >= small_count:
            ptype = "SMALL"
        else:
            ptype = "BIG"

    # Random number for display (0-9)
    pnum = random.randint(0, 9)

    # Make sure number matches type (so it looks consistent)
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
        except Exception:
            pass
        time.sleep(3)
    return "NO_RESULT", None, None


# ═══════════════════════════════════════════════════════════════
# ✅ WAIT UNTIL XX:00 (next minute boundary)
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

    print("🤖 Rexx Predictor Bot Started — Infinite Mode")
    send_text(
        "🤖 *Bot Started — WinGo 1M Clock Mode*\n"
        "♾️ Infinite · Never stops\n"
        "⏰ Prediction @ XX:00 · Result @ XX+1:00"
    )

    # Initial wait: align to next minute boundary
    wait_until_next_minute()

    while True:
        try:
            # ─── STEP A: Get latest period → next period = latest + 1 ───
            latest = get_latest_period()
            if not latest:
                print("⚠️ API failed, retry in 20s...")
                time.sleep(20)
                continue

            try:
                next_period = str(int(latest) + 1)
            except Exception:
                time.sleep(20)
                continue

            # ─── STEP B: Skip if same period already predicted ───
            if next_period == last_predicted_period:
                print(f"⚠️ Same period {next_period}, waiting 30s...")
                time.sleep(30)
                continue

            # ─── STEP C: Make prediction ───
            ptype, pnumber = make_random_prediction()
            print(f"\n{'=' * 55}")
            print(f"📊 Period: {next_period} | Prediction: {pnumber} ({ptype})")
            print(f"🏆 Score: {total_wins}W / {total_losses}L")

            # ─── STEP D: Send prediction to Telegram ───
            send_prediction(next_period, ptype, pnumber, total_wins, total_losses)
            last_predicted_period = next_period

            # ─── STEP E: Wait until next minute boundary (XX:00) ───
            wait_until_next_minute()

            # ─── STEP F: Check result ───
            print(f"🔍 Checking result for period {next_period}...")
            result, actual_num, actual_type = check_result(
                next_period, ptype, pnumber, timeout_sec=75
            )

            # ─── STEP G: Send result to Telegram ───
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

            # ─── STEP H: Small buffer before next cycle ───
            time.sleep(3)

        except KeyboardInterrupt:
            # User manually stopped — bot WILL NOT stop on its own
            send_text(
                f"🛑 *Bot stopped manually*\n"
                f"🏆 Final: {total_wins}W / {total_losses}L"
            )
            print(f"\n🛑 Stopped. Score: {total_wins}W / {total_losses}L")
            break

        except Exception as e:
            # Any error → just log, keep running
            print(f"⚠️ Loop error: {e}")
            time.sleep(10)


# ═══════════════════════════════════════════════════════════════
# ENTRY
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
