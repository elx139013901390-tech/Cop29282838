import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

from database import *
from questions import QUESTIONS

TOKEN = os.getenv("BOT_TOKEN")

NAME1, AGE1, NAME2, AGE2, QUESTION = range(5)

users = {}

init_db()


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    add_user(user.id, user.username, user.first_name)

    users[user.id] = {}

    await update.message.reply_text(
        "❤️ تست عشق شروع شد\n\nنام نفر اول را وارد کن:"
    )

    return NAME1


# ---------------- NAME1 ----------------
async def get_name1(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    users[uid]["name1"] = update.message.text

    await update.message.reply_text("سن نفر اول را وارد کن:")

    return AGE1


# ---------------- AGE1 ----------------
async def get_age1(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    users[uid]["age1"] = update.message.text

    await update.message.reply_text("نام نفر دوم را وارد کن:")

    return NAME2


# ---------------- NAME2 ----------------
async def get_name2(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    users[uid]["name2"] = update.message.text

    await update.message.reply_text("سن نفر دوم را وارد کن:")

    return AGE2


# ---------------- AGE2 ----------------
async def get_age2(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    users[uid]["age2"] = update.message.text

    users[uid]["score"] = 0
    users[uid]["question"] = 0

    await update.message.reply_text(
        QUESTIONS[0] + "\n\nعدد 1 تا 5 وارد کن."
    )

    return QUESTION


# ---------------- QUESTION SYSTEM ----------------
async def question(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    try:
        answer = int(update.message.text)

        if answer < 1 or answer > 5:
            await update.message.reply_text("فقط عدد 1 تا 5 وارد کن.")
            return QUESTION

    except:
        await update.message.reply_text("فقط عدد وارد کن.")
        return QUESTION

    users[uid]["score"] += answer
    users[uid]["question"] += 1

    q = users[uid]["question"]

    # هنوز سوال داریم
    if q < len(QUESTIONS):

        await update.message.reply_text(
            QUESTIONS[q] + "\n\nعدد 1 تا 5 وارد کن."
        )

        return QUESTION

    # ---------------- RESULT ----------------
    total = len(QUESTIONS) * 5

    love = int((users[uid]["score"] / total) * 100)

    trust = min(100, love + 5)
    respect = min(100, love + 3)
    loyalty = min(100, love + 7)
    jealousy = max(0, 100 - love)

    marriage = max(0, love - 10)
    breakup = max(0, 100 - love)

    if love >= 80:
        result = "❤️ رابطه عالی"
    elif love >= 60:
        result = "💚 رابطه خوب"
    elif love >= 40:
        result = "💛 رابطه متوسط"
    else:
        result = "💔 رابطه ضعیف"

    save_test(
        uid,
        users[uid]["name1"],
        users[uid]["age1"],
        users[uid]["name2"],
        users[uid]["age2"],
        love,
        trust,
        respect,
        loyalty,
        jealousy,
        marriage,
        breakup,
        result
    )

    await update.message.reply_text(f"""
❤️ نتیجه تست عشق

👤 {users[uid]['name1']}
❤️
👤 {users[uid]['name2']}

💘 درصد عشق: {love}%

🤝 اعتماد: {trust}%
💖 احترام: {respect}%
🛡 وفاداری: {loyalty}%
😒 حسادت: {jealousy}%

💍 احتمال ازدواج: {marriage}%
💔 احتمال جدایی: {breakup}%

📊 نتیجه:
{result}

سازنده:
امیر علی فروزان اصل
""")

    return ConversationHandler.END


# ---------------- CANCEL ----------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END


# ---------------- MAIN ----------------
app = Application.builder().token(TOKEN).build()

conv = ConversationHandler(

    entry_points=[
        CommandHandler("start", start)
    ],

    states={

        NAME1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name1)],
        AGE1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age1)],
        NAME2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name2)],
        AGE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age2)],
        QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, question)]

    },

    fallbacks=[
        CommandHandler("cancel", cancel)
    ]
)

app.add_handler(conv)

print("Bot is running...")

app.run_polling()
