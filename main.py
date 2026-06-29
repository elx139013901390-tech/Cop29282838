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
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB = "bot.db"

# ================= DB =================
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
async def get_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.json()
            return data.get(symbol, {}).get("usd")

# ================= USER =================
async def add_user(user):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES (?)",
            (user.id,)
        )
        await db.commit()

# ================= MENU =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪙 قیمت", callback_data="price")],
        [InlineKeyboardButton("⭐ علاقه‌مندی‌ها", callback_data="fav")],
        [InlineKeyboardButton("🔔 هشدار", callback_data="alert")],
        [InlineKeyboardButton("👑 پنل ادمین", callback_data="admin")],
        [InlineKeyboardButton("💰 سکه من", callback_data="coins")],
        [InlineKeyboardButton("📈 نمودار", callback_data="chart")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_user(update.effective_user)
    await update.message.reply_text("💎 ربات VIP فعال شد", reply_markup=menu())

# ================= FAVORITE =================
async def add_favorite(user_id, symbol):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO favorites VALUES (?,?)",
            (user_id, symbol)
        )
        await db.commit()

# ================= ALERT =================
async def add_alert(user_id, symbol, target):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO alerts VALUES (?,?,?)",
            (user_id, symbol, target)
        )
        await db.commit()

# ================= COINS =================
async def get_coins(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT coins FROM users WHERE user_id=?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

# ================= CALLBACK =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    # ---------- PRICE ----------
    if q.data == "price":
        price = await get_price("bitcoin")
        await q.edit_message_text(f"🪙 Bitcoin: ${price}", reply_markup=menu())

    # ---------- FAVORITE ----------
    elif q.data == "fav":
        await add_favorite(user_id, "bitcoin")
        await q.edit_message_text("⭐ به علاقه‌مندی اضافه شد")

    # ---------- ALERT ----------
    elif q.data == "alert":
        await add_alert(user_id, "bitcoin", 50000)
        await q.edit_message_text("🔔 هشدار روی 50000 ثبت شد")

    # ---------- COINS ----------
    elif q.data == "coins":
        coins = await get_coins(user_id)
        await q.edit_message_text(f"💰 سکه شما: {coins}")

    # ---------- ADMIN ----------
    elif q.data == "admin":
        if user_id != ADMIN_ID:
            return await q.edit_message_text("⛔ دسترسی نداری")

        await q.edit_message_text("👑 پنل ادمین:\n/users /stats")

    # ---------- CHART ----------
    elif q.data == "chart":
        prices = [40000, 42000, 41000, 45000, 47000]

        plt.plot(prices)
        plt.title("Bitcoin Trend")
        plt.savefig("chart.png")

        with open("chart.png", "rb") as f:
            await q.message.reply_photo(f)

# ================= PRICE CHECKER =================
async def price_worker(app):
    while True:
        await asyncio.sleep(20)

        async with aiosqlite.connect(DB) as db:
            async with db.execute("SELECT * FROM alerts") as cur:
                alerts = await cur.fetchall()

        for user_id, symbol, target in alerts:
            price = await get_price(symbol)

            if price and price >= target:
                await app.bot.send_message(
                    user_id,
                    f"🚨 هشدار فعال شد!\n{symbol}: ${price}"
                )

# ================= MAIN =================
async def main():
    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    asyncio.create_task(price_worker(app))

    print("VIP Bot Running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
