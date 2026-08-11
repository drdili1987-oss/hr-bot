from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

router = Router(name="onboarding")

ONBOARDING_STEPS = [
    (
        "rules",
        "📋 <b>Kompaniya qoidalari va dress-code</b>\n\n"
        "• Ish vaqti: 09:00–18:00, Dush-Juma\n"
        "• Dress-code: business casual\n"
        "• Kechikish haqida menejerni oldindan xabardor qiling",
    ),
    (
        "first_day",
        "🗓 <b>Birinchi ish kuni</b>\n\n"
        "• 09:00 — HR bilan uchrashuv, hujjatlarni rasmiylashtirish\n"
        "• 10:00 — Jamoa va mentor bilan tanishuv\n"
        "• Mentoringiz: kontaktni HR yuboradi",
    ),
    (
        "faq",
        "❓ <b>Tez-tez so'raladigan savollar</b>\n\n"
        "• Ish haqi qachon to'lanadi? — Har oyning 10-sanasida\n"
        "• Ta'til qanday rasmiylashtiriladi? — Mentoringiz orqali HR'ga so'rov\n"
        "• Savollar bo'lsa — /help buyrug'idan foydalaning",
    ),
]


def onboarding_kb(index: int) -> InlineKeyboardMarkup:
    buttons = []
    if index < len(ONBOARDING_STEPS) - 1:
        buttons.append(
            InlineKeyboardButton(text="Keyingisi ➡️", callback_data=f"onb_next_{index + 1}")
        )
    return InlineKeyboardMarkup(inline_keyboard=[buttons] if buttons else [])


@router.message(Command("onboarding"))
async def cmd_onboarding(message: Message) -> None:
    title, text = ONBOARDING_STEPS[0]
    await message.answer(text, reply_markup=onboarding_kb(0))


@router.callback_query(F.data.startswith("onb_next_"))
async def onboarding_next(callback: CallbackQuery) -> None:
    index = int(callback.data.split("_")[-1])
    if index >= len(ONBOARDING_STEPS):
        await callback.answer()
        return
    title, text = ONBOARDING_STEPS[index]
    await callback.message.edit_text(text, reply_markup=onboarding_kb(index))
    await callback.answer()
