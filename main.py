import os
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
        await db.commit()

async def add_user(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES (?)",
            (user_id,)
        )
        await db.commit()

async def get_coins(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT coins FROM users WHERE user_id=?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

# ================= API =================
async def get_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.json()
            return data["bitcoin"]["usd"]

# ================= UI =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪙 قیمت بیت‌کوین", callback_data="price")],
        [InlineKeyboardButton("💰 سکه من", callback_data="coins")],
        [InlineKeyboardButton("⭐ علاقه‌مندی", callback_data="fav")],
        [InlineKeyboardButton("👑 ادمین", callback_data="admin")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await add_user(user_id)

    await update.message.reply_text(
        "👋 خوش آمدی به ربات حرفه‌ای",
        reply_markup=menu()
    )

# ================= CALLBACK =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    if q.data == "price":
        price = await get_price()
        await q.edit_message_text(f"🪙 Bitcoin: ${price}", reply_markup=menu())

    elif q.data == "coins":
        coins = await get_coins(user_id)
        await q.edit_message_text(f"💰 سکه شما: {coins}", reply_markup=menu())

    elif q.data == "fav":
        await q.edit_message_text("⭐ اضافه شد به علاقه‌مندی (نسخه ساده)", reply_markup=menu())

    elif q.data == "admin":
        if user_id != ADMIN_ID:
            await q.edit_message_text("⛔ دسترسی نداری")
        else:
            await q.edit_message_text("👑 پنل ادمین فعال است", reply_markup=menu())

# ================= MAIN (FIXED FOR RAILWAY) =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
