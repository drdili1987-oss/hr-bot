from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")

HELP_TEXT = (
    "🆘 <b>Yordam</b>\n\n"
    "/start — Botni ishga tushirish va menyuni ochish\n"
    "/onboarding — Yangi xodimlar uchun moslashtirish bo'limi\n"
    "/help — Ushbu yordam xabari\n\n"
    "HR bo'limi bilan bog'lanish: @hr_department"
)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)
