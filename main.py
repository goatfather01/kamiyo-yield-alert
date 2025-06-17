import requests
import os
import datetime
import asyncio
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
        response.raise_for_status()

        try:
            data = response.json()
        except Exception as json_err:
            bot.send_message(chat_id=CHAT_ID, text=f"❌ JSON parse error: {json_err}")
            return None, None, None

        # Send the first few vaults as debug
        sample = data[:3] if isinstance(data, list) else data
        bot.send_message(chat_id=CHAT_ID, text=f"📦 Raw API preview:\n{sample}")

        for vault in data:
            if vault.get("symbol") == "JUPSOL/SOL":
                lst_apy = float(vault["lstApy"]) * 100
                borrow_apy = float(vault["solBorrowApy"]) * 100
                spread = lst_apy - borrow_apy
                return lst_apy, borrow_apy, spread

        return None, None, None
    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"❌ API Exception: {e}")
        return None, None, None

async def send_alert():
    try:
        lst_apy, borrow_apy, spread = get_apy_data()
    except Exception as e:
        await bot.send_message(chat_id=CHAT_ID, text=f"❌ API exception: {e}")
        return

    await bot.send_message(chat_id=CHAT_ID, text="✅ Bot test: I'm alive and connected!")

    if lst_apy is None:
        await bot.send_message(chat_id=CHAT_ID, text="⚠️ Failed to fetch Kamino data or vault not found.")
        return

    message = f"""
🧠 JUPSOL/SOL Yield Report ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}):
• JUPSOL APY: {lst_apy:.2f}%
• SOL Borrow APY: {borrow_apy:.2f}%
• Spread: {spread:.2f}%
"""

    if spread <= 0:
        message += "🚨 NEGATIVE YIELD! Consider exiting."
    elif spread < 1:
        message += "⚠️ Warning: Spread < 1%"
    else:
        message += "✅ You're in the green."

    await bot.send_message(chat_id=CHAT_ID, text=message)

# Trigger immediately when the script runs
asyncio.run(send_alert())
