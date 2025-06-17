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
        url = "https://api.kamino.finance/vaults"
        response = requests.get(url)
        data = response.json()

        for vault in data:
            if vault.get("symbol") == "JUPSOL/SOL":
                lst_apy = float(vault["lstApy"]) * 100
                borrow_apy = float(vault["solBorrowApy"]) * 100
                spread = lst_apy - borrow_apy
                return lst_apy, borrow_apy, spread

        print("⚠️ JUPSOL/SOL vault not found.")
        return None, None, None

    except Exception as e:
        print("⚠️ API exception:", e)
        return None, None, None

def send_alert():
    lst_apy, borrow_apy, spread = get_apy_data()
    if lst_apy is None:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Failed to fetch Kamino data.")
        return

    message = f"""
🧠 JUPSOL/SOL Yield Report ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}):
• JUPSOL APY: {lst_apy:.2f}%
• SOL Borrow APY: {borrow_apy:.2f}%
• Spread: {spread:.2f}%
"""

    if spread <= 0:
        message += "🚨 **NEGATIVE YIELD!** You’re losing money. Consider exiting."
    elif spread < 1:
        message += "⚠️ **Warning:** Spread < 1%. Close to turning negative."
    else:
        message += "✅ Everything looks good. You're in the green."

    bot.send_message(chat_id=CHAT_ID, text=message)

send_alert()
