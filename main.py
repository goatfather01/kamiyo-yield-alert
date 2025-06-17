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

# Replace with actual tokenMint for JUPSOL if available
JUPSOL_MINT = "mSoLzYCxHdYgdzU16g50Sh3i5K3z3KZK7ytfqcJm7So"

# --- Kamino Staking Yield API Call ---
def get_jupsol_apy():
    try:
        url = "https://api.kamino.finance/v2/staking-yields"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for item in data:
            if item.get("tokenMint") == JUPSOL_MINT:
                apy = float(item.get("apy", 0)) * 100
                return apy

        return None
    except Exception as e:
        return f"❌ API Error: {e}"

# --- Telegram Bot Alert ---
async def send_alert():
    result = get_jupsol_apy()

    if isinstance(result, str):  # error string
        await bot.send_message(chat_id=CHAT_ID, text=result)
        return

    if result is None:
        await bot.send_message(chat_id=CHAT_ID, text="⚠️ JUPSOL not found in staking-yields API.")
        return

    message = f"""
📊 JUPSOL Staking Yield Report ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}):
• JUPSOL APY: {result:.2f}%
"""

    await bot.send_message(chat_id=CHAT_ID, text=message)

# Run it immediately for GitHub Actions
asyncio.run(send_alert())
