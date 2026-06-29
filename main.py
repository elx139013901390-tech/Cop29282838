import os
import asyncio
import aiohttp
import aiosqlite
import matplotlib.pyplot as plt

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB = "bot.db"

# ================= DATABASE =================
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 100
        )
        """)

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
            target REAL
        )
        """)

        await db.commit()

# ================= API =================
async def crypto_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.json()
            return data.get(symbol, {}).get("usd")

async def fiat_convert(from_c, to_c):
    url = f"https://api.exchangerate.host/convert?from={from_c}&to={to_c}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.json()
            return data.get("result")

# ================= DB HELPERS =================
async def add_user(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR IGNORE INTO users VALUES (?,100)", (user_id,))
        await db.commit()

async def get_coins(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT coins FROM users WHERE user_id=?", (user_id,)) as c:
            row = await c.fetchone()
            return row[0] if row else 0

async def add_fav(user_id, symbol):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT INTO favorites VALUES (?,?)", (user_id, symbol))
        await db.commit()

async def add_alert(user_id, symbol, target):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT INTO alerts VALUES (?,?,?)", (user_id, symbol, target))
        await db.commit()

# ================= UI =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪙 قیمت BTC", callback_data="price")],
        [InlineKeyboardButton("💱 تبدیل ارز", callback_data="fiat")],
        [InlineKeyboardButton("⭐ علاقه‌مندی", callback_data="fav")],
        [InlineKeyboardButton("🔔 هشدار", callback_data="alert")],
        [InlineKeyboardButton("💰 سکه", callback_data="coins")],
        [InlineKeyboardButton("📊 نمودار", callback_data="chart")],
        [InlineKeyboardButton("👑 ادمین", callback_data="admin")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_user(update.effective_user.id)
    await update.message.reply_text("🚀 GOD BOT فعال شد", reply_markup=menu())

# ================= CALLBACK =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if q.data == "price":
        price = await crypto_price("bitcoin")
        await q.edit_message_text(f"🪙 BTC: ${price}", reply_markup=menu())

    elif q.data == "fiat":
        result = await fiat_convert("usd", "eur")
        await q.edit_message_text(f"💱 USD → EUR: {result}", reply_markup=menu())

    elif q.data == "fav":
        await add_fav(uid, "bitcoin")
        await q.edit_message_text("⭐ اضافه شد", reply_markup=menu())

    elif q.data == "alert":
        await add_alert(uid, "bitcoin", 50000)
        await q.edit_message_text("🔔 هشدار ثبت شد", reply_markup=menu())

    elif q.data == "coins":
        coins = await get_coins(uid)
        await q.edit_message_text(f"💰 سکه: {coins}", reply_markup=menu())

    elif q.data == "chart":
        data = [40000, 42000, 41000, 45000, 47000]

        plt.plot(data)
        plt.title("BTC")
        plt.savefig("chart.png")

        with open("chart.png", "rb") as f:
            await q.message.reply_photo(f)

    elif q.data == "admin":
        if uid != ADMIN_ID:
            await q.edit_message_text("⛔ دسترسی نداری")
        else:
            await q.edit_message_text("👑 پنل GOD فعال شد", reply_markup=menu())

# ================= PRICE CHECKER =================
async def checker(app):
    while True:
        await asyncio.sleep(30)

        async with aiosqlite.connect(DB) as db:
            async with db.execute("SELECT * FROM alerts") as c:
                rows = await c.fetchall()

        for uid, sym, target in rows:
            price = await crypto_price(sym)

            if price and price >= target:
                await app.bot.send_message(uid, f"🚨 ALERT: {sym} = ${price}")

# ================= MAIN =================
async def main():
    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    asyncio.create_task(checker(app))

    print("🔥 GOD BOT RUNNING...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
