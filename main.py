import requests
import os
import datetime
import asyncio
from telegram import Bot

print("🔁 Kamino bot starting...")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print(f"BOT_TOKEN is {'✅ SET' if BOT_TOKEN else '❌ MISSING'}")
print(f"CHAT_ID is {'✅ SET' if CHAT_ID else '❌ MISSING'}")

bot = Bot(token=BOT_TOKEN)

# ✅ JUPSOL tokenMint
JUPSOL_MINT = "jupSoLaHXQiZZTSfEWMTRRgpnyFm8f6sZdosWBjx93v"
MARKET_PUBKEY = "7u3HeHxYDLhnCoErrtycNokbQYbWGzLs6JSDqGAv5PfF"
RESERVE_PUBKEY = "d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q"

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
        return f"❌ JUPSOL APY API Error: {e}"

def get_sol_borrow_apy():
    try:
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        url = f"https://api.kamino.finance/kamino-market/{MARKET_PUBKEY}/reserves/{RESERVE_PUBKEY}/metrics/history"
        params = {
            "env": "mainnet-beta",
            "start": yesterday.isoformat(),
            "end": today.isoformat(),
            "frequency": "hour"
        }

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

async def send_alert():
    jupsol_apy = get_jupsol_apy()
    sol_borrow_apy = get_sol_borrow_apy()

    if isinstance(jupsol_apy, str):
        print(jupsol_apy)
        await bot.send_message(chat_id=CHAT_ID, text=jupsol_apy)
        return
    if isinstance(sol_borrow_apy, str):
        print(sol_borrow_apy)
        await bot.send_message(chat_id=CHAT_ID, text=sol_borrow_apy)
        return
    if jupsol_apy is None or sol_borrow_apy is None:
        warning = "⚠️ Missing APY data from Kamino."
        print(warning)
        await bot.send_message(chat_id=CHAT_ID, text=warning)
        return

    spread = jupsol_apy - sol_borrow_apy

    message = f"""
📊 JUPSOL/SOL Yield Report ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}):
• JUPSOL APY: {jupsol_apy:.2f}%
• SOL Borrow APY: {sol_borrow_apy:.2f}%
• Net Spread: {spread:.2f}%
"""

    if spread <= 0:
        message += "🚨 NEGATIVE YIELD – consider exiting!"
    elif spread < 1:
        message += "⚠️ Warning: Spread < 1% – monitor closely."
    else:
        message += "✅ All good – you're in profit."

    print("✅ Sending Telegram alert...")
    await bot.send_message(chat_id=CHAT_ID, text=message)

try:
    asyncio.run(send_alert())
except Exception as e:
    print("❌ Fatal Error in bot:", e)
