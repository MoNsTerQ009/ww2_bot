from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏭 کارخانه‌ها", callback_data="factories")],
        [InlineKeyboardButton(text="🛒 آرسنال (شاپ)", callback_data="shop")],
        [InlineKeyboardButton(text="⚔️ حمله", callback_data="attack")],
        [InlineKeyboardButton(text="🤝 اتحاد (به زودی)", callback_data="alliance")],
        [InlineKeyboardButton(text="📊 آمار من", callback_data="stats")]
    ])

def country_selection(countries):
    buttons = []
    for country in countries:
        buttons.append([InlineKeyboardButton(text=country, callback_data=f"select_country_{country}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)