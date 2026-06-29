import os
import aiohttp
import aiosqlite

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

# ---------------- DATABASE ----------------
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0
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


async def add_user(user):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id, username) VALUES (?,?)",
            (user.id, user.username)
        )
        await db.commit()

# ---------------- API ----------------
async def get_fiat_rate(from_cur, to_cur):
    url = f"https://api.exchangerate.host/convert?from={from_cur}&to={to_cur}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.json()
            return data.get("result", 0)


async def get_crypto_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.json()
            return data.get(symbol, {}).get("usd")


async def get_country(name):
    url = f"https://restcountries.com/v3.1/name/{name}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.json()

            if isinstance(data, list):
                c = data[0]
                currency = list(c.get("currencies", {}).keys())[0] if c.get("currencies") else "N/A"

                return (
                    f"🌍 کشور: {c['name']['common']}\n"
                    f"💰 واحد پول: {currency}\n"
                    f"👥 جمعیت: {c['population']}\n"
                    f"🌐 قاره: {c['region']}"
                )

            return "یافت نشد"

# ---------------- UI ----------------
menu = ReplyKeyboardMarkup([
    ["💱 تبدیل ارز", "🪙 کریپتو"],
    ["🌍 کشور", "👤 پروفایل"],
    ["👑 پنل ادمین"]
], resize_keyboard=True)

# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_user(update.effective_user)
    await update.message.reply_text("👋 خوش آمدی!", reply_markup=menu)


async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, amount, f, t = update.message.text.split()
        result = await get_fiat_rate(f.upper(), t.upper())
        await update.message.reply_text(f"💱 نتیجه: {float(amount) * result} {t}")
    except:
        await update.message.reply_text("مثال: convert 10 USD EUR")


async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, symbol = update.message.text.split()
        price = await get_crypto_price(symbol.lower())
        await update.message.reply_text(f"🪙 {symbol}: ${price}")
    except:
        await update.message.reply_text("مثال: crypto bitcoin")


async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, name = update.message.text.split(maxsplit=1)
        data = await get_country(name)
        await update.message.reply_text(data)
    except:
        await update.message.reply_text("مثال: country germany")


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👤 آیدی: {user.id}\n"
        f"👤 یوزرنیم: @{user.username}"
    )


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ دسترسی نداری")

    await update.message.reply_text("👑 پنل ادمین فعال است")

# ---------------- MAIN ----------------
async def main():
    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^convert"), convert))
    app.add_handler(MessageHandler(filters.Regex("^crypto"), crypto))
    app.add_handler(MessageHandler(filters.Regex("^country"), country))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("admin", admin))

    print("Bot is running...")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
