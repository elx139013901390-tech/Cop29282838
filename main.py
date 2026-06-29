from modules.currency import get_rates
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN

keyboard = ReplyKeyboardMarkup(
    [
        ["💱 ارزهای جهان", "🪙 ارزهای دیجیتال"],
        ["🌍 کشورها", "🔄 تبدیل ارز"],
        ["⭐ علاقه‌مندی‌ها", "👤 پروفایل"],
        ["📈 بازارها", "⚙️ تنظیمات"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 به ربات بازارهای مالی خوش آمدید.",
        reply_markup=keyboard
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "💱 ارزهای جهان":
        await update.message.reply_text("در حال دریافت قیمت ارزها...")
        async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "💱 ارزهای جهان":

        rates = get_rates()

        if not rates:
            await update.message.reply_text("❌ خطا در دریافت قیمت")
            return

        msg = f"""
💱 قیمت لحظه‌ای ارزها

🇺🇸 USD : {rates['USD']}
🇪🇺 EUR : {rates['EUR']}
🇬🇧 GBP : {rates['GBP']}
🇯🇵 JPY : {rates['JPY']}
🇨🇳 CNY : {rates['CNY']}
🇹🇷 TRY : {rates['TRY']}
🇷🇺 RUB : {rates['RUB']}
🇦🇪 AED : {rates['AED']}
🇸🇦 SAR : {rates['SAR']}
🇮🇷 IRR : {rates['IRR']}
"""

        await update.message.reply_text(msg)

    elif text == "🪙 ارزهای دیجیتال":
        await update.message.reply_text("در حال دریافت قیمت ارزهای دیجیتال...")

    elif text == "🪙 ارزهای دیجیتال":
        await update.message.reply_text("در حال دریافت قیمت ارزهای دیجیتال...")

    elif text == "🌍 کشورها":
        await update.message.reply_text("نام کشور را ارسال کنید.")

    elif text == "🔄 تبدیل ارز":
        await update.message.reply_text("مثال:\n100 USD EUR")

    elif text == "👤 پروفایل":
        await update.message.reply_text("پروفایل شما")

    else:
        await update.message.reply_text("این بخش در حال تکمیل است.")

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))

print("Bot Started...")

app.run_polling()
