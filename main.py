# main.py

import os
import requests
import datetime

print("🔁 Kamino bot starting...")

# --- Configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

JUPSOL_MINT = "jupSoLaHXQiZZTSfEWMTRRgpnyFm8f6sZdosWBjx93v"
MARKET_PUBKEY = "7u3HeHxYDLhnCoErrtycNokbQYbWGzLs6JSDqGAv5PfF"
RESERVE_PUBKEY = "d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q"
# --- End Configuration ---


def send_telegram_message(message):
    """Sends a message to Telegram using the requests library."""
    print("✅ Preparing to send Telegram alert...")
    # Check if secrets are present
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ FATAL: BOT_TOKEN or CHAT_ID is not set in GitHub Secrets.")
        # Exit with a non-zero code to make the GitHub Action fail
        exit(1)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'  # Optional: for formatting like *bold*
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # This will raise an error for non-2xx responses
        print("✅ Telegram alert sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send Telegram message: {e}")
        # Also fail the action if the message can't be sent
        exit(1)


def get_jupsol_apy():
    # This function is unchanged, it was already perfect.
    try:
        url = "https://api.kamino.finance/v2/staking-yields"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        for item in data:
            if item.get("tokenMint") == JUPSOL_MINT:
                return float(item.get("apy", 0)) * 100
        return None
    except Exception as e:
        return f"❌ JUPSOL APY API Error: {e}"


def get_sol_borrow_apy():
    # This function is also unchanged.
    try:
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        url = f"https://api.kamino.finance/kamino-market/{MARKET_PUBKEY}/reserves/{RESERVE_PUBKEY}/metrics/history"
        params = {"env": "mainnet-beta", "start": yesterday.isoformat(), "end": today.isoformat(), "frequency": "hour"}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "history" in data and data["history"]:
            last_entry = data["history"][-1]
            return float(last_entry["metrics"].get("borrowInterestAPY", 0)) * 100
        else:
            return None
    except Exception as e:
        return f"❌ SOL Borrow APY API Error: {e}"


# --- Main script execution ---
if __name__ == "__main__":
    jupsol_apy = get_jupsol_apy()
    sol_borrow_apy = get_sol_borrow_apy()

    # Handle API errors
    if isinstance(jupsol_apy, str) or isinstance(sol_borrow_apy, str) or jupsol_apy is None or sol_borrow_apy is None:
        error_message = f"⚠️ Could not retrieve data.\nJUP-SOL: {jupsol_apy}\nSOL Borrow: {sol_borrow_apy}"
        print(error_message)
        send_telegram_message(error_message)
    else:
        # If data is good, calculate spread and build message
        spread = jupsol_apy - sol_borrow_apy
        message = (
            f"📊 *JUPSOL/SOL Yield Report* ({datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')})\n"
            f"• JUPSOL APY: `{jupsol_apy:.2f}%`\n"
            f"• SOL Borrow APY: `{sol_borrow_apy:.2f}%`\n"
            f"• *Net Spread: {spread:.2f}%*\n\n"
        )

        if spread <= 0:
            message += "🚨 *NEGATIVE YIELD* – consider exiting!"
        elif spread < 1:
            message += "⚠️ *Warning: Spread < 1%* – monitor closely."
        else:
            message += "✅ *All good* – you're in profit."
        
        send_telegram_message(message)

    print("✅ Bot finished.")
