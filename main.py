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

# ✅ Correct JUPSOL tokenMint
JUPSOL_MINT = "jupSoLaHXQiZZTSfEWMTRRgpnyFm8f6sZdosWBjx93v"

# --- JUPSOL APY from staking-yields API ---
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

# --- SOL Borrow Rate from vaults API ---
def get_sol_borrow_apy():
    try:
        url = "https://api.kamino.finance/vaults/v2?category=multiply"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for vault in data:
            if vault.get("symbol") == "JUPSOL/SOL":
                return float(vault.get("solBorrowApy", 0)) * 100
        return None
    except Exception as e:
        return f"❌ SOL Borrow APY API Error: {e}"

# --- Telegram Bot Alert ---
async def send_alert():
    jupsol_apy = get_jupsol_apy()
    sol_borrow_apy = get_sol_borrow_apy()

    # Error handling
    if isinstance(jupsol_apy, str):
        await bot.send_message(chat_id=CHAT_ID, text=jupsol_apy)
        return
    if isinstance(sol_borrow_apy, str):
        await bot.send_message(chat_id=CHAT_ID, text=sol_borrow_apy)
        return
    if jupsol_apy is None or sol_borrow_apy is None:
        await bot.send_message(chat_id=CHAT_ID, text="⚠️ Missing APY data from Kamino.")
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

    await bot.send_message(chat_id=CHAT_ID, text=message)

# Run it immediately for GitHub Actions
asyncio.run(send_alert())
