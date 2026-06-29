import os
import json
import asyncio
import aiohttp
import aiosqlite
import websockets

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ================== CONFIG ==================
TOKEN = os.getenv("TOKEN")
DB = "bot.db"

latest_prices = {}

# ================== DATABASE ==================
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            symbol TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            user_id INTEGER,
            symbol TEXT,
            price REAL
        )
        """)
        await db.commit()

# ================== CRYPTO PRICE (REST fallback) ==================
async def crypto_price(symbol="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.json()
            return data.get(symbol, {}).get("usd", 0)

# ================== FIAT CONVERT ==================
async def fiat_convert(from_cur="USD", to_cur="EUR", amount=1):
    url = f"https://api.exchangerate.host/convert?from={from_cur}&to={to_cur}&amount={amount}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.json()
            return data.get("result", 0)

# ================== BINANCE WEBSOCKET ==================
async def binance_ws():
    url = "wss://stream.binance.com:9443/ws/!ticker@arr"

    async with websockets.connect(url) as ws:
        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            for item in data:
                symbol = item["s"]
                price = float(item["c"])
                latest_prices[symbol] = price

# ================== ALERT SYSTEM ==================
async def alert_checker(app):
    while True:
        async with aiosqlite.connect(DB) as db:
            cur = await db.execute("SELECT user_id, symbol, price FROM alerts")
            rows = await cur.fetchall()

        for user_id, symbol, target in rows:
            sym = symbol.upper() + "USDT"
            price = latest_prices.get(sym)

            if price and price >= target:
                await app.bot.send_message(
                    chat_id=user_id,
                    text=f"🚨 ALERT!\n{symbol} reached {price}$ 🎯"
                )

        await asyncio.sleep(10)

# ================== UI ==================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 BTC Price", callback_data="btc")],
        [InlineKeyboardButton("💱 Convert USD→EUR", callback_data="convert")],
        [InlineKeyboardButton("📈 Chart", callback_data="chart")],
        [InlineKeyboardButton("⭐ Favorites", callback_data="fav")]
    ])

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 GOD CRYPTO BOT\n👑 Amir Ali Faroozan Asl",
        reply_markup=menu()
    )

# ================== CALLBACK ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    # -------- BTC PRICE --------
    if q.data == "btc":
        price = latest_prices.get("BTCUSDT", None)

        if not price:
            price = await crypto_price("bitcoin")

        await q.message.reply_text(f"💰 BTC: {price}$")

    # -------- CONVERT --------
    elif q.data == "convert":
        result = await fiat_convert("USD", "EUR", 10)
        await q.message.reply_text(f"💱 10 USD = {result} EUR")

    # -------- CHART (QuickChart API) --------
    elif q.data == "chart":
        url = "https://quickchart.io/chart?c={type:'line',data:{labels:['1','2','3','4'],datasets:[{label:'BTC',data:[10,20,15,30]}]}}"
        await q.message.reply_text(f"📈 Chart:\n{url}")

    # -------- FAVORITES --------
    elif q.data == "fav":
        await q.message.reply_text("⭐ Favorites system ready (DB enabled)")

# ================== ALERT COMMAND ==================
async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        symbol = context.args[0]
        price = float(context.args[1])

        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "INSERT INTO alerts VALUES (?,?,?)",
                (user_id, symbol, price)
            )
            await db.commit()

        await update.message.reply_text("✅ Alert saved!")

    except:
        await update.message.reply_text("❌ Use: /alert BTC 50000")

# ================== MAIN ==================
async def main():
    await init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CallbackQueryHandler(buttons))

    asyncio.create_task(binance_ws())
    asyncio.create_task(alert_checker(app))

    print("💎 GOD BOT RUNNING...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
