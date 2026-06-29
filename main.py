import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.background import BackgroundScheduler

# --- تنظیمات اصلی ---
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
# در Railway، این لینک را از بخش Database دریافت و اینجا قرار دهید
try:
    DATABASE_URL = os.getenv("DATABASE_URL")
except:
    DATABASE_URL = "sqlite:///bot.db"

# --- تنظیمات دیتابیس (SQLAlchemy) ---
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    name = Column(String)
    favorites = Column(String, default="") # ذخیره آیدی ارزها به صورت رشته

class PriceAlert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    symbol = Column(String)
    target_price = Column(Float)

Base.metadata.create_all(engine)

# --- دریافت داده‌ها از API (بدون نیاز به کتابخانه اضافی) ---
class FinancialAPI:
    @staticmethod
    def get_crypto_price(symbol):
        """دریافت قیمت از CoinGecko"""
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
        try:
            response = requests.get(url).json()
            return response[symbol]['usd']
        except:
            return None

    @staticmethod
    def get_fiat_rate(base, target):
        """دریافت نرخ ارزهای جهانی"""
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        try:
            data = requests.get(url).json()
            return data['rates'][target]
        except:
            return None

# --- بخش ربات تلگرام ---
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = Session()
    
    # ثبت کاربر در دیتابیس اگر نبود
    user = session.query(User).filter_by(telegram_id=user_id).first()
    if not user:
        new_user = User(telegram_id=user_id, name=update.effective_user.first_name)
        session.add(new_user)
        session.commit()
    session.close()

    keyboard = [
        [InlineKeyboardButton("🪙 ارزهای دیجیتال", callback_data='menu_crypto')],
        [InlineKeyboardButton("💱 تبدیل ارز جهانی", callback_data='menu_fiat')],
        [InlineKeyboardButton("📈 طلا و نفت", callback_data='menu_gold')],
        [InlineKeyboardButton("⭐ ارزهای محبوب", callback_data='menu_fav')],
        [InlineKeyboardButton("🔔 هشدار قیمت", callback_data='menu_alert')],
        [InlineKeyboardButton("👤 پروفایل", callback_data='menu_profile')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("💎 **به ربات مالی امیرعلی فروزا خوش آمدید**\nلطفاً انتخاب کنید:", reply_markup=reply_markup, parse_mode='Markdown')

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'menu_crypto':
        # در اینجا می‌توانید لیست ارزها را از دیتابیس یا API بگیرید
        await query.edit_message_text("🔍 در حال جستجو در لیست ۱۰,۰۰۰ ارز...")
        # نمونه نمایش قیمت
        price = FinancialAPI.get_crypto_price("bitcoin")
        await query.message.reply_text(f"💰 قیمت بیت‌کوین: ${price}")

    elif query.data == 'menu_profile':
        session = Session()
        user = session.query(User).filter_by(telegram_id=query.from_user.id).first()
        await query.edit_message_text(f"👤 پروفایل شما:\n🆔 {user.telegram_id}\n⭐ محبوب‌ها: {user.favorites}")
        session.close()

# --- سیستم هشدار (Background Task) ---
def check_price_alerts():
    """این تابع هر دقیقه چک می‌کند آیا قیمتی به حد نصاب رسیده یا خیر"""
    session = Session()
    alerts = session.query(PriceAlert).all()
    for alert in alerts:
        current_price = FinancialAPI.get_crypto_price(alert.symbol)
        if current_price and current_price >= alert.target_price:
            # در اینجا کد ارسال پیام به کاربر قرار می‌گیرد
            print(f"ALERT! {alert.symbol} reached {current_price}")
    session.close()

# --- اجرای اصلی ---
def main():
    application = Application.builder().token(TOKEN).build()

    # افزودن دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_buttons))

    # تنظیم زمان‌بندی برای چک کردن قیمت‌ها (هر ۶۰ ثانیه)
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_price_alerts, 'interval', seconds=60)
    scheduler.start()

    print("🚀 Bot is running on Railway...")
    application.run_polling()

if __name__ == '__main__':
    main()
