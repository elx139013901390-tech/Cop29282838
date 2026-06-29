import os
import asyncio
import aiohttp
import aiosqlite

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")
DB = "bot.db"

# ================= DB =================
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0
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
            price REAL
        )
        """)
        await db.commit()

async def add_user(user_id: int):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        await db.commit()

# ================= BINANCE API =================
async def get_price(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            return float(data["price"])

# ================= UI =================
def kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 قیمت BTC", callback_data="price")],
        [InlineKeyboardButton("⭐ علاقه‌مندی", callback_data="fav")],
        [InlineKeyboardButton("🔔 هشدار", callback_data="alert")],
        [InlineKeyboardButton("💎 سکه", callback_data="coins")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await add_user(user_id)

    await update.message.reply_text(
        "💎 ربات GOD کریپتو فعال شد",
        reply_markup=kb()
    )

# ================= CALLBACK =================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id

    if q.data == "price":
        price = await get_price("BTCUSDT")
        await q.edit_message_text(f"💰 BTC:\n{price}$")

    elif q.data == "coins":
        async with aiosqlite.connect(DB) as db:
            cur = await db.execute(
                "SELECT coins FROM users WHERE user_id=?",
                (user_id,)
            )
            row = await cur.fetchone()
            coins = row[0] if row else 0

        await q.edit_message_text(f"💎 سکه: {coins}")

    elif q.data == "fav":
        async with aiosqlite.connect(DB) as db:
            cur = await db.execute(
                "SELECT symbol FROM favorites WHERE user_id=?",
                (user_id,)
            )
            rows = await cur.fetchall()

        text = "\n".join([r[0] for r in rows]) if rows else "خالی"
        await q.edit_message_text(f"⭐ علاقه‌مندی‌ها:\n{text}")

    elif q.data == "alert":
        await q.edit_message_text("🔔 استفاده:\n/alert BTCUSDT 40000")

# ================= ALERT COMMAND =================
async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        symbol = context.args[0]
        price = float(context.args[1])
    except:
        await update.message.reply_text("❌ مثال: /alert BTCUSDT 40000")
        return

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO alerts VALUES (?,?,?)",
            (user_id, symbol, price)
        )
        await db.commit()

    await update.message.reply_text("✅ هشدار ثبت شد")

# ================= BACKGROUND TASK =================
async def checker(app):
    while True:
        async with aiosqlite.connect(DB) as db:
            cur = await db.execute("SELECT user_id, symbol, price FROM alerts")
            rows = await cur.fetchall()

        for user_id, symbol, target in rows:
            try:
                price = await get_price(symbol)
                if price >= target:
                    await app.bot.send_message(
                        user_id,
                        f"🚨 ALERT!\n{symbol} = {price}$"
                    )
            except:
                pass

        await asyncio.sleep(30)

# ================= MAIN =================
async def main():
    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CallbackQueryHandler(callback))

    asyncio.create_task(checker(app))

    print("BOT RUNNING...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
