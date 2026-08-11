from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
import typing

BTN_APPLY = "💼 Vakansiyalarga topshirish"
BTN_OPEN_CANDIDACY = "🙋‍♂️ O'zimni tavsiya qilaman"
BTN_ABOUT = "ℹ️ Kompaniya haqida"
BTN_SHARE_PHONE = "📱 Kontaktni yuborish"
BTN_CANCEL = "❌ Bekor qilish"
BTN_ADMIN_STATS = "📊 Statistika"
BTN_ADMIN_EXPORT = "📥 Nomzodlarni yuklab olish"
BTN_ADMIN_BROADCAST = "✉️ Xabar yuborish"
BTN_ADMIN_ADD_VACANCY = "➕ Vakansiya qo'shish"
BTN_ADMIN_DEL_VACANCY = "🗑 Vakansiyani o'chirish"
BTN_ADMIN_VIEW_APPS = "📂 Arizalarni ko'rish"

# Forms
BTN_SKIP_RESUME = "⏭ Rezyumesiz davom etish"
BTN_GENERATE_RESUME = "📝 Bot orqali rezyume yaratish"


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_APPLY), KeyboardButton(text=BTN_OPEN_CANDIDACY)],
            [KeyboardButton(text=BTN_ABOUT)],
        ],
        resize_keyboard=True,
    )


def phone_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_SHARE_PHONE, request_contact=True)],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
    )


def cancel_only_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )


def resume_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_GENERATE_RESUME)],
            [KeyboardButton(text=BTN_SKIP_RESUME)],
            [KeyboardButton(text=BTN_CANCEL)]
        ],
        resize_keyboard=True,
    )


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADMIN_VIEW_APPS)],
            [KeyboardButton(text=BTN_ADMIN_ADD_VACANCY), KeyboardButton(text=BTN_ADMIN_DEL_VACANCY)],
            [KeyboardButton(text=BTN_ADMIN_STATS), KeyboardButton(text=BTN_ADMIN_EXPORT)],
            [KeyboardButton(text=BTN_ADMIN_BROADCAST)],
        ],
        resize_keyboard=True,
    )


def vacancies_inline_kb(vacancies: list[dict], action: str = "apply") -> InlineKeyboardMarkup:
    # action: "apply" for applying to a vacancy, "del" for deleting a vacancy in admin panel
    buttons = []
    for row in vacancies:
        btn = InlineKeyboardButton(
            text=row['title'],
            callback_data=f"vac_{action}_{row['id']}"
        )
        buttons.append([btn])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def vacancy_details_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ushbu vakansiyaga topshirish", callback_data=f"vac_apply_{vacancy_id}")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="vac_back_list")]
        ]
    )


def candidate_pagination_kb(candidate_index: int, total_count: int, filter_val: str = "all") -> InlineKeyboardMarkup:
    buttons = []
    if candidate_index > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"cand_prev_{candidate_index - 1}_{filter_val}"))
    if candidate_index < total_count - 1:
        buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"cand_next_{candidate_index + 1}_{filter_val}"))
        
    return InlineKeyboardMarkup(inline_keyboard=[buttons] if buttons else [])


def admin_vacancy_filter_kb(vacancies: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for row in vacancies:
        btn = InlineKeyboardButton(
            text=row['title'],
            callback_data=f"filter_vac_{row['id']}"
        )
        buttons.append([btn])
    
    buttons.append([InlineKeyboardButton(text="📋 Barcha arizalar", callback_data="filter_vac_all")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
