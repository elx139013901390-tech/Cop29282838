import os
import json
import aiohttp
import asyncio
import aiosqlite
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

DB = "bot.db"

# ---------------- DATABASE ----------------
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


# ---------------- PRICE API (BINANCE REAL) ----------------
async def get_price(symbol="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            return data[symbol]["usd"]


# ---------------- FIAT ----------------
async def fiat_convert(amount, from_cur, to_cur):
    url = f"https://api.exchangerate.host/convert?from={from_cur}&to={to_cur}&amount={amount}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            return data["result"]


# ---------------- CHART (NO matplotlib) ----------------
def chart_url(prices):
    base = "https://quickchart.io/chart"
    config = {
        "type": "line",
        "data": {
            "labels": list(range(len(prices))),
            "datasets": [{
                "label": "Price",
                "data": prices
            }]
        }
    }
    return f"{base}?c={json.dumps(config)}"


# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 ربات کریپتو فعال شد\n"
        "دستورها:\n"
        "/price bitcoin\n"
        "/convert 10 usd eur"
    )


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = context.args[0] if context.args else "bitcoin"
    p = await get_price(coin)
    await update.message.reply_text(f"💰 {coin.upper()} = ${p}")


async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = float(context.args[0])
    f = context.args[1]
    t = context.args[2]
    result = await fiat_convert(amount, f, t)
    await update.message.reply_text(f"💱 {result} {t}")


# ---------------- ALERT CHECK LOOP ----------------
async def alert_loop(app):
    while True:
        async with aiosqlite.connect(DB) as db:
            async with db.execute("SELECT * FROM alerts") as cur:
                rows = await cur.fetchall()

        for user_id, symbol, target in rows:
            try:
                price = await get_price(symbol)
                if price >= target:
                    await app.bot.send_message(
                        user_id,
                        f"🔔 ALERT!\n{symbol} رسید به {price}$"
                    )
            except:
                pass

        await asyncio.sleep(30)


# ---------------- MAIN ----------------
async def main():
    if not TOKEN:
        print("❌ BOT_TOKEN تنظیم نشده!")
        return

    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("convert", convert))

    asyncio.create_task(alert_loop(app))

    print("🚀 Bot Running...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
