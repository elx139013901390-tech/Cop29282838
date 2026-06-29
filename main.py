import random
import aiosqlite
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "YOUR_BOT_TOKEN"
DB = "love.db"

user_data = {}

# ---------------- DB ----------------
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT
        )
        """)
        await db.commit()


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💖 ربات عشق فعال شد!\n\n"
        "برای شروع بنویس:\n"
        "/love"
    )


# ---------------- LOVE START ----------------
async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {}

    await update.message.reply_text("💘 اسم خودت را وارد کن:")


# ---------------- MESSAGE FLOW ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data:
        return

    data = user_data[user_id]

    # step 1
    if "me" not in data:
        data["me"] = text
        await update.message.reply_text("💌 اسم طرف مقابل؟")
        return

    # step 2
    if "you" not in data:
        data["you"] = text
        await update.message.reply_text("🎂 سن خودت؟")
        return

    # step 3
    if "age1" not in data:
        data["age1"] = text
        await update.message.reply_text("🎂 سن طرف مقابل؟")
        return

    # step 4
    if "age2" not in data:
        data["age2"] = text

        # 💘 CALCULATION
        base = random.randint(40, 95)

        # سن تاثیر
        try:
            a1 = int(data["age1"])
            a2 = int(data["age2"])
            diff = abs(a1 - a2)

            if diff < 3:
                base += 5
            elif diff > 10:
                base -= 10
        except:
            pass

        percent = min(max(base, 0), 100)

        # تحلیل
        if percent > 80:
            status = "💖 عشق واقعی و قوی!"
        elif percent > 50:
            status = "💛 رابطه متوسط ولی قابل رشد"
        else:
            status = "💔 بیشتر احساسی لحظه‌ایه"

        await update.message.reply_text(
            f"💘 نتیجه عشق‌سنج\n\n"
            f"👤 {data['me']} ❤️ {data['you']}\n\n"
            f"📊 درصد عشق: {percent}%\n"
            f"🔮 تحلیل: {status}\n\n"
            f"👑 ساخته شده توسط: امیر علی فروزان اصل"
        )

        user_data.pop(user_id)
        return


# ---------------- MAIN ----------------
async def main():
    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("💖 Bot Running...")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
