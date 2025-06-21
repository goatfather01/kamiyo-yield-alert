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
RESERVE_PUBKEY = "d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q" # This is the SOL reserve
KAMINO_URL = "https://app.kamino.finance/earn/multiply/7u3HeHxYDLhnCoErrtycNokbQYbWGzLs6JSDqGAv5PfF/DGQZWCY17gGtBUgdaFs1VreJWsodkjFxndPsskwFKGpp/d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q"
# --- End Configuration ---


def send_telegram_message(message):
    """Sends a message to Telegram using the requests library."""
    print("✅ Preparing to send Telegram alert...")
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ FATAL: BOT_TOKEN or CHAT_ID is not set in GitHub Secrets.")
        exit(1)

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("✅ Telegram alert sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send Telegram message: {e}")
        exit(1)


def get_jupsol_apy():
    """Fetches the JUPSOL staking yield."""
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
    """
    Fetches the current SOL Borrow APY directly from the market's reserve data.
    This is more robust than using the historical endpoint.
    """
    try:
        # This URL fetches the current state of all reserves in the market
        url = f"https://api.kamino.finance/kamino-market/{MARKET_PUBKEY}"
        params = {"env": "mainnet-beta"}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Loop through the reserves to find the one we want (SOL)
        for reserve in data.get("reserves", []):
            if reserve.get("reserveAddress") == RESERVE_PUBKEY:
                # The APY is directly available in the 'borrowApy' field
                return float(reserve.get("borrowApy", 0)) * 100
        
        # If the reserve wasn't found for some reason
        return None
        
    except Exception as e:
        # We can make the error message a bit more informative
        return f"❌ SOL Borrow APY API Error: {e}"


# --- Main script execution ---
if __name__ == "__main__":
    jupsol_apy = get_jupsol_apy()
    sol_borrow_apy = get_sol_borrow_apy()

    if isinstance(jupsol_apy, str) or isinstance(sol_borrow_apy, str) or jupsol_apy is None or sol_borrow_apy is None:
        # Format the values for cleaner error display
        jupsol_display = f"{jupsol_apy:.4f}" if isinstance(jupsol_apy, float) else jupsol_apy
        sol_display = f"{sol_borrow_apy:.4f}" if isinstance(sol_borrow_apy, float) else sol_borrow_apy
        
        error_message = f"⚠️ Could not retrieve all data.\n\nJUP-SOL: {jupsol_display}\nSOL Borrow: {sol_display}"
        print(error_message)
        send_telegram_message(error_message)
    else:
        spread = jupsol_apy - sol_borrow_apy
        message = (
            f"📊 *JUPSOL/SOL Yield Report* ({datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')})\n\n"
            f"• JUPSOL APY: `{jupsol_apy:.2f}%`\n"
            f"• SOL Borrow APY: `{sol_borrow_apy:.2f}%`\n\n"
            f"• *Net Spread: {spread:.2f}%*\n\n"
        )

        if spread <= 0:
            message += "🚨 *NEGATIVE YIELD* – consider exiting!"
        elif spread < 1:
            message += "⚠️ *Warning: Spread < 1%* – monitor closely."
        else:
            message += "✅ *All good* – you're in profit."
        
        message += f"\n\n[Website Click Here]({KAMINO_URL})"
        
        send_telegram_message(message)

    print("✅ Bot finished.")
