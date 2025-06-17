import requests
import os
import datetime
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=BOT_TOKEN)

def get_apy_data():
    try:
        url = "https://api.kamino.finance/vaults/v2?category=multiply"
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTP error if failed
        data = response.json()

        for vault in data:
            if vault.get("symbol") == "JUPSOL/SOL":
                lst_apy = float(vault["lstApy"]) * 100
                borrow_apy = float(vault["solBorrowApy"]) * 100
                spread = lst_apy - borrow_apy
                return lst_apy, borrow_apy, spread

        return None, None, None
    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"❌ API Error: {e}")
        return None, None, None

def send_alert():
    lst_apy, borrow_apy, spread = get_apy_data()

    # Force debug output to Telegram
    if lst_apy is None:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ No data returned or vault not found.")
        return

    message = f"""
🔍 DEBUG: JUPSOL/SOL Yield
Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
JUPSOL APY: {lst_apy:.2f}%
SOL Borrow APY: {borrow_apy:.2f}%
Spread: {spread:.2f}%
"""

    if spread <= 0:
        message += "🚨 NEGATIVE YIELD – consider exiting!"
    elif spread < 1:
        message += "⚠️ Warning: Spread < 1%"
    else:
        message += "✅ All good."

    bot.send_message(chat_id=CHAT_ID, text=message)

# Run once immediately
send_alert()
