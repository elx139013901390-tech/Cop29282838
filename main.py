import os
import asyncio
import aiohttp
import aiosqlite
import matplotlib.pyplot as plt

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB = "bot.db"


# ---------------- DB ----------------
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
            coin TEXT
        )
        """)
        await db.commit()


async def add_user(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id, coins) VALUES (?,0)",
            (user_id,)
        )
        await db.commit()


async def add_coin(user_id, amount=1):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "UPDATE users SET coins = coins + ? WHERE user_id=?",
            (amount, user_id)
        )
        await db.commit()


async def get_coin(user_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else 0


async def add_favorite(user_id, coin):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO favorites(user_id, coin) VALUES (?,?)",
            (user_id, coin.upper())
        )
        await db.commit()


async def get_favorites(user_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT coin FROM favorites WHERE user_id=?", (user_id,))
        return [row[0] for row in await cur.fetchall()]


# ---------------- API ----------------
async def get_price(coin="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            return data.get(coin, {}).get("usd", 0)


# ---------------- KEYBOARD ----------------
keyboard = ReplyKeyboardMarkup([
    ["💰 سکه", "⭐ علاقه‌مندی"],
    ["📊 قیمت بیتکوین", "🔔 هشدار قیمت"],
    ["👑 پنل ادمین"]
], resize_keyboard=True)


# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await add_user(user_id)

    await update.message.reply_text("💎 ربات کریپتو فعال شد", reply_markup=keyboard)


async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    await add_user(user_id)
    await add_coin(user_id, 1)

    # 💰 coins
    if text == "💰 سکه":
        coins = await get_coin(user_id)
        await update.message.reply_text(f"💰 سکه: {coins}")

    # ⭐ favorites
    elif text == "⭐ علاقه‌مندی":
        fav = await get_favorites(user_id)
        await update.message.reply_text(f"⭐ ارزهای ذخیره شده: {fav}")

    # 📊 price
    elif text == "📊 قیمت بیتکوین":
        price = await get_price("bitcoin")
        await update.message.reply_text(f"📊 BTC: ${price}")

    # 🔔 alert test
    elif text == "🔔 هشدار قیمت":
        price = await get_price("bitcoin")
        if price > 0:
            await update.message.reply_text(f"🔔 قیمت فعلی BTC: ${price}")

    # 👑 admin
    elif text == "👑 پنل ادمین":
        if user_id == ADMIN_ID:
            await update.message.reply_text("👑 پنل ادمین فعال")
        else:
            await update.message.reply_text("❌ دسترسی ندارید")


# ---------------- MAIN ----------------
async def main():
    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))

    print("BOT RUNNING...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
