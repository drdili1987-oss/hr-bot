from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_ID
from database import get_active_vacancies
from keyboards import BTN_ABOUT, BTN_APPLY, BTN_OPEN_CANDIDACY, admin_menu_kb, cancel_only_kb, main_menu_kb, vacancies_inline_kb
from states import RecruitingForm

router = Router(name="start")

ABOUT_TEXT = (
    "🏢 <b>Kompaniya haqida</b>\n\n"
    "Biz — tez rivojlanayotgan IT kompaniyamiz. Jamoamizga qo'shilish uchun "
    "\"💼 Vakansiyalarga topshirish\" tugmasini bosing va qisqa anketani to'ldiring."
)

WELCOME_TEXT = (
    "👋 Assalomu alaykum! HR botiga xush kelibsiz.\n\n"
    "Bu yerda siz bo'sh vakansiyalarga ariza topshirishingiz mumkin. "
    "Quyidagi menyudan kerakli bo'limni tanlang."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "👨‍💻 <b>Admin paneliga xush kelibsiz!</b>\n\nQuyidagi menyudan kerakli bo'limni tanlang:",
            reply_markup=admin_menu_kb()
        )
    else:
        await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.message(F.text == BTN_ABOUT)
async def about_company(message: Message) -> None:
    await message.answer(ABOUT_TEXT)


@router.message(F.text == BTN_OPEN_CANDIDACY)
async def process_open_candidacy(message: Message, state: FSMContext) -> None:
    await state.set_state(RecruitingForm.custom_vacancy)
    await message.answer(
        "🙋‍♂️ Qaysi soha mutaxassisisiz? O'zingiz qiziqqan yo'nalish yoki lavozimni kiriting (masalan: Grafik dizayner):",
        reply_markup=cancel_only_kb()
    )


@router.message(F.text == BTN_APPLY)
async def start_application(message: Message, state: FSMContext) -> None:
    await state.clear()
    vacancies = await get_active_vacancies()
    
    if not vacancies:
        await message.answer("😔 Hozircha ochiq vakansiyalar yo'q. Iltimos, keyinroq urinib ko'ring.")
        return
        
    await message.answer(
        "💼 Qaysi vakansiyaga topshirmoqchisiz? Quyidagilardan birini tanlang:",
        reply_markup=vacancies_inline_kb(vacancies, action="view")
    )
