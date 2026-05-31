import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import Database
from keyboards import main_menu, country_selection, shop_menu, attack_menu

load_dotenv()
logging.basicConfig(level=logging.INFO)

# توکن ربات از فایل .env خوانده می‌شود
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = Database()

# ========== دستور استارت ==========
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    if user_data:
        # کاربر قبلاً ثبت‌نام کرده
        await message.answer(
            f"🎖️ خوش برگشتی ژنرال {user_data['country']}!\n"
            f"💰 پول: {user_data['money']}\n"
            f"🏭 فولاد: {user_data['steel']} | ⛽ نفت: {user_data['oil']}\n"
            f"🔬 فناوری: {user_data['tech']}",
            reply_markup=main_menu()
        )
    else:
        # کاربر جدید: نمایش کشورهای موجود
        available_countries = db.get_available_countries()
        await message.answer(
            "🌟 به بازی ژنرال‌های جنگ جهانی دوم خوش آمدی!\n\n"
            "لطفاً کشور خود را انتخاب کنید:",
            reply_markup=country_selection(available_countries)
        )

# ========== انتخاب کشور ==========
@dp.callback_query(lambda c: c.data.startswith("select_country_"))
async def select_country(callback: CallbackQuery):
    user_id = callback.from_user.id
    country_name = callback.data.replace("select_country_", "")
    
    # بررسی اینکه کشور قبلاً گرفته نشده باشد
    if not db.is_country_available(country_name):
        await callback.answer("⛔ این کشور قبلاً توسط ژنرال دیگری انتخاب شده!", show_alert=True)
        return
    
    # ثبت کاربر
    db.register_user(user_id, callback.from_user.username or "ناشناس", country_name)
    
    await callback.message.edit_text(
        f"✅ تبریک! شما ژنرال {country_name} شدید.\n\n"
        f"🏭 یک کارخانه فولاد و یک کارخانه نفت به عنوان هدیه دریافت کردید.\n"
        f"هر 24 ساعت یک بار می‌توانید سود کارخانه‌ها را برداشت کنید."
    )
    await callback.message.answer(
        f"🎖️ پنل فرماندهی {country_name}\n"
        f"💰 پول: 1000 | 🏭 فولاد: 100 | ⛽ نفت: 100 | 🔬 فناوری: 0",
        reply_markup=main_menu()
    )

# ========== منوی اصلی: کارخانه‌ها ==========
@dp.callback_query(lambda c: c.data == "factories")
async def show_factories(callback: CallbackQuery):
    user_data = db.get_user(callback.from_user.id)
    if not user_data:
        await callback.answer("لطفاً ابتدا /start را بزنید")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏭 ساخت کارخانه فولاد (500 پول)", callback_data="build_steel_factory")],
        [InlineKeyboardButton(text="⛽ ساخت کارخانه نفت (500 پول)", callback_data="build_oil_factory")],
        [InlineKeyboardButton(text="🔬 ساخت آزمایشگاه فناوری (1000 پول)", callback_data="build_lab")],
        [InlineKeyboardButton(text="📦 برداشت سود روزانه", callback_data="collect_profit")],
        [InlineKeyboardButton(text="🔙 برگشت", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        f"🏭 **مدیریت کارخانه‌ها**\n\n"
        f"کارخانه فولاد: {user_data['steel_factories']} عدد (تولید روزانه 50-100 فولاد)\n"
        f"کارخانه نفت: {user_data['oil_factories']} عدد (تولید روزانه 40-80 نفت)\n"
        f"آزمایشگاه: {user_data['labs']} عدد (تولید روزانه 5-15 فناوری)",
        reply_markup=keyboard
    )

# ========== ساخت کارخانه ==========
@dp.callback_query(lambda c: c.data in ["build_steel_factory", "build_oil_factory", "build_lab"])
async def build_factory(callback: CallbackQuery):
    user_id = callback.from_user.id
    factory_type = callback.data
    
    if factory_type == "build_steel_factory":
        result = db.build_steel_factory(user_id)
    elif factory_type == "build_oil_factory":
        result = db.build_oil_factory(user_id)
    else:
        result = db.build_lab(user_id)
    
    if result["success"]:
        await callback.answer(result["message"], show_alert=True)
        # بروزرسانی پیام
        await show_factories(callback)
    else:
        await callback.answer(result["message"], show_alert=True)

# ========== برداشت سود روزانه ==========
@dp.callback_query(lambda c: c.data == "collect_profit")
async def collect_profit(callback: CallbackQuery):
    user_id = callback.from_user.id
    result = db.collect_daily_profit(user_id)
    
    if result["success"]:
        await callback.answer(
            f"✅ برداشت شد!\n🏭 فولاد: +{result['steel']}\n⛽ نفت: +{result['oil']}\n🔬 فناوری: +{result['tech']}",
            show_alert=True
        )
        await show_factories(callback)
    else:
        await callback.answer(result["message"], show_alert=True)

# ========== شاپ ==========
@dp.callback_query(lambda c: c.data == "shop")
async def show_shop(callback: CallbackQuery):
    user_data = db.get_user(callback.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔫 تفنگ (50 پول)", callback_data="buy_rifle")],
        [InlineKeyboardButton(text="💣 تانک (200 فولاد + 100 پول)", callback_data="buy_tank")],
        [InlineKeyboardButton(text="✈️ هواپیما (200 نفت + 150 پول)", callback_data="buy_plane")],
        [InlineKeyboardButton(text="🔬 ارتقاء فناوری (50 فناوری)", callback_data="upgrade_tech")],
        [InlineKeyboardButton(text="🔙 برگشت", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        f"🛒 **آرسنال جنگی**\n\n"
        f"💰 پول: {user_data['money']}\n"
        f"🏭 فولاد: {user_data['steel']} | ⛽ نفت: {user_data['oil']}\n"
        f"🔬 فناوری: {user_data['tech']}\n"
        f"⚔️ نیروها: تفنگ {user_data['rifles']} | تانک {user_data['tanks']} | هواپیما {user_data['planes']}",
        reply_markup=keyboard
    )

# ========== خرید از شاپ ==========
@dp.callback_query(lambda c: c.data.startswith("buy_") or c.data == "upgrade_tech")
async def buy_item(callback: CallbackQuery):
    user_id = callback.from_user.id
    item = callback.data
    
    result = db.purchase_item(user_id, item)
    await callback.answer(result["message"], show_alert=True)
    
    if result["success"]:
        await show_shop(callback)

# ========== حمله ==========
@dp.callback_query(lambda c: c.data == "attack")
async def attack_menu_handler(callback: CallbackQuery):
    user_data = db.get_user(callback.from_user.id)
    
    # لیست کشورهای دیگر (به جز خود کاربر)
    other_countries = db.get_other_countries(user_data["country"])
    
    if not other_countries:
        await callback.answer("هیچ کشور دیگری برای حمله وجود ندارد!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚔️ {c}", callback_data=f"target_{c}")] for c in other_countries
    ] + [[InlineKeyboardButton(text="🔙 برگشت", callback_data="back_to_menu")]])
    
    await callback.message.edit_text(
        f"🎯 **حمله به چه کشوری؟**\n\n"
        f"نیروهای شما:\n"
        f"🔫 تفنگ: {user_data['rifles']} | 💣 تانک: {user_data['tanks']} | ✈️ هواپیما: {user_data['planes']}",
        reply_markup=keyboard
    )

# ========== انتخاب هدف حمله ==========
@dp.callback_query(lambda c: c.data.startswith("target_"))
async def choose_target(callback: CallbackQuery):
    target_country = callback.data.replace("target_", "")
    user_data = db.get_user(callback.from_user.id)
    
    # ذخیره هدف در یک دیتا (می‌توان از FSM استفاده کرد، اینجا ساده شده)
    # برای سادگی: از کاربر می‌خواهیم تعداد نیروها را تایپ کند
    
    await callback.message.answer(
        f"🎯 **هدف: {target_country}**\n\n"
        f"نیروهای شما:\n"
        f"🔫 تفنگ: {user_data['rifles']}\n"
        f"💣 تانک: {user_data['tanks']}\n"
        f"✈️ هواپیما: {user_data['planes']}\n\n"
        f"لطفاً تعداد نیروهای اعزامی را به صورت زیر وارد کنید:\n"
        f"`تفنگ:10 تانک:5 هواپیما:2`\n\n"
        f"(حداکثر مقداری که دارید می‌توانید بفرستید)",
        parse_mode="Markdown"
    )
    
    # ذخیره هدف در حافظه موقت (می‌توان از دیتابیس استفاده کرد)
    # اینجا ساده شده - در پروژه واقعی از FSM aiogram استفاده کن
    db.set_pending_attack(callback.from_user.id, target_country)

# ========== دریافت فرم حمله ==========
@dp.message()
async def handle_attack_form(message: Message):
    user_id = message.from_user.id
    pending = db.get_pending_attack(user_id)
    
    if not pending:
        # پیام عادی - می‌توان منوی اصلی را نشان داد
        return
    
    # پردازش فرم حمله (مثال: "تفنگ:10 تانک:5 هواپیما:2")
    import re
    rifles = int(re.search(r'تفنگ:(\d+)', message.text).group(1)) if re.search(r'تفنگ:(\d+)', message.text) else 0
    tanks = int(re.search(r'تانک:(\d+)', message.text).group(1)) if re.search(r'تانک:(\d+)', message.text) else 0
    planes = int(re.search(r'هواپیما:(\d+)', message.text).group(1)) if re.search(r'هواپیما:(\d+)', message.text) else 0
    
    user_data = db.get_user(user_id)
    
    # بررسی موجودی کافی
    if rifles > user_data["rifles"] or tanks > user_data["tanks"] or planes > user_data["planes"]:
        await message.answer("❌ موجودی نیروهای شما کافی نیست!")
        db.clear_pending_attack(user_id)
        return
    
    # ارسال درخواست به ادمین برای تأیید
    admin_text = (
        f"⚔️ **درخواست حمله جدید** ⚔️\n\n"
        f"🎖️ از: {user_data['country']} (@{message.from_user.username or 'بدون یوزرنیم'})\n"
        f"🎯 به: {pending['target']}\n\n"
        f"نیروهای اعزامی:\n"
        f"🔫 تفنگ: {rifles}\n"
        f"💣 تانک: {tanks}\n"
        f"✈️ هواپیما: {planes}\n\n"
        f"تعداد نیروهای باقیمانده مهاجم:\n"
        f"🔫 تفنگ: {user_data['rifles'] - rifles} | 💣 تانک: {user_data['tanks'] - tanks} | ✈️ هواپیما: {user_data['planes'] - planes}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تأیید حمله", callback_data=f"approve_attack_{user_id}_{pending['target']}_{rifles}_{tanks}_{planes}")],
        [InlineKeyboardButton(text="❌ رد حمله", callback_data=f"reject_attack_{user_id}")]
    ])
    
    await bot.send_message(ADMIN_ID, admin_text, reply_markup=keyboard, parse_mode="Markdown")
    await message.answer("✅ درخواست حمله به ادمین ارسال شد. منتظر تأیید باشید...")
    db.clear_pending_attack(user_id)

# ========== ادمین: تأیید حمله ==========
@dp.callback_query(lambda c: c.data.startswith("approve_attack_"))
async def approve_attack(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ فقط ادمین می‌تواند حملات را تأیید کند!", show_alert=True)
        return
    
    parts = callback.data.split("_")
    attacker_id = int(parts[2])
    target_country = parts[3]
    rifles = int(parts[4])
    tanks = int(parts[5])
    planes = int(parts[6])
    
    # اجرای حمله
    result = db.execute_attack(attacker_id, target_country, rifles, tanks, planes)
    
    # اطلاع‌رسانی به مهاجم
    await bot.send_message(
        attacker_id,
        f"⚔️ **نتیجه حمله به {target_country}** ⚔️\n\n"
        f"{result['message']}\n\n"
        f"تلفات شما: {result['attacker_losses']}\n"
        f"تلفات دشمن: {result['defender_losses']}\n\n"
        f"غارت: {result['loot']}"
    )
    
    # اطلاع‌رسانی به مدافع (اگر آنلاین باشد)
    defender = db.get_user_by_country(target_country)
    if defender:
        await bot.send_message(
            defender["user_id"],
            f"⚠️ **شما مورد حمله قرار گرفتید!** ⚠️\n\n"
            f"🎖️ مهاجم: {result['attacker_country']}\n\n"
            f"{result['defender_message']}\n\n"
            f"تلفات شما: {result['defender_losses']}"
        )
    
    await callback.message.edit_text(f"✅ حمله تأیید و اجرا شد.\n{result['message']}")
    await callback.answer("حمله با موفقیت اجرا شد!")

# ========== ادمین: رد حمله ==========
@dp.callback_query(lambda c: c.data.startswith("reject_attack_"))
async def reject_attack(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ فقط ادمین!", show_alert=True)
        return
    
    attacker_id = int(callback.data.split("_")[2])
    await bot.send_message(attacker_id, "❌ درخواست حمله شما توسط ادمین رد شد.")
    await callback.message.edit_text("❌ حمله رد شد.")
    await callback.answer("حمله رد شد!")

# ========== برگشت به منوی اصلی ==========
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    user_data = db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"🎖️ پنل فرماندهی {user_data['country']}\n"
        f"💰 پول: {user_data['money']}\n"
        f"🏭 فولاد: {user_data['steel']} | ⛽ نفت: {user_data['oil']}\n"
        f"🔬 فناوری: {user_data['tech']}",
        reply_markup=main_menu()
    )

# ========== اجرای ربات ==========
async def main():
    print("🤖 ربات ژنرال‌های جنگ جهانی دوم روشن شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())