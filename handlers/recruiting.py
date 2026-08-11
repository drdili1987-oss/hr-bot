import os
import logging
import re

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import (
    ALLOWED_RESUME_EXTENSIONS,
    ALLOWED_RESUME_MIME_TYPES,
    HR_GROUP_ID,
    MAX_RESUME_SIZE_MB,
    ADMIN_ID
)
from database import save_candidate as add_candidate
from keyboards import (
    BTN_CANCEL,
    BTN_SKIP_RESUME,
    BTN_GENERATE_RESUME,
    cancel_only_kb,
    main_menu_kb,
    phone_request_kb,
    resume_request_kb,
    vacancy_details_kb,
    vacancies_inline_kb
)
from states import RecruitingForm
from resume_generator import generate_pdf_resume

logger = logging.getLogger(__name__)
router = Router(name="recruiting")


def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"[^\d]", "", raw)
    if digits.startswith("998") and len(digits) == 12:
        return "+" + digits
    if len(digits) == 9:
        return "+998" + digits
    return None


@router.message(RecruitingForm.full_name, F.text == BTN_CANCEL)
@router.message(RecruitingForm.phone, F.text == BTN_CANCEL)
@router.message(RecruitingForm.experience, F.text == BTN_CANCEL)
@router.message(RecruitingForm.resume, F.text == BTN_CANCEL)
@router.message(RecruitingForm.custom_vacancy, F.text == BTN_CANCEL)
@router.message(RecruitingForm.gen_photo, F.text == BTN_CANCEL)
@router.message(RecruitingForm.gen_birth_year, F.text == BTN_CANCEL)
@router.message(RecruitingForm.gen_address, F.text == BTN_CANCEL)
@router.message(RecruitingForm.gen_education, F.text == BTN_CANCEL)
@router.message(RecruitingForm.gen_languages, F.text == BTN_CANCEL)
@router.message(RecruitingForm.gen_previous_work, F.text == BTN_CANCEL)
@router.message(RecruitingForm.gen_skills, F.text == BTN_CANCEL)
@router.message(RecruitingForm.gen_expected_salary, F.text == BTN_CANCEL)
async def cancel_application(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Ariza bekor qilindi.", reply_markup=main_menu_kb())


# --- Step 1: Vacancy Selection and Full name ---
@router.callback_query(F.data.startswith("vac_view_"))
async def process_vacancy_view(callback: CallbackQuery) -> None:
    from database import get_active_vacancies
    vacancies = await get_active_vacancies()
    vacancy_id = int(callback.data.split("_")[2])
    
    vacancy = next((v for v in vacancies if v['id'] == vacancy_id), None)
    if not vacancy:
        await callback.answer("Vakansiya topilmadi.", show_alert=True)
        return
        
    text = (
        f"📋 <b>Vakansiya:</b> {vacancy['title']}\n\n"
        f"📝 <b>Ma'lumot:</b>\n{vacancy['description']}"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=vacancy_details_kb(vacancy_id)
    )
    await callback.answer()


@router.callback_query(F.data == "vac_back_list")
async def process_vacancy_back(callback: CallbackQuery) -> None:
    from database import get_active_vacancies
    vacancies = await get_active_vacancies()
    if not vacancies:
        await callback.message.edit_text("😔 Hozircha ochiq vakansiyalar yo'q.")
        return
    await callback.message.edit_text(
        "💼 Qaysi vakansiyaga topshirmoqchisiz? Quyidagilardan birini tanlang:",
        reply_markup=vacancies_inline_kb(vacancies, action="view")
    )
    await callback.answer()

@router.message(RecruitingForm.custom_vacancy, F.text.len() >= 2)
async def process_custom_vacancy(message: Message, state: FSMContext) -> None:
    vacancy_title = message.text.strip()
    await state.update_data(vacancy_title=vacancy_title)
    await state.set_state(RecruitingForm.full_name)
    await message.answer(
        f"✅ Tanlangan soha: <b>{vacancy_title}</b>\n\n"
        "1/4. Ism va familiyangizni to'liq kiriting (masalan: Toshmatov Eshmat):",
        reply_markup=cancel_only_kb()
    )

@router.message(RecruitingForm.custom_vacancy)
async def process_custom_vacancy_invalid(message: Message) -> None:
    await message.answer("Soha nomini to'g'ri kiriting.")

@router.callback_query(F.data.startswith("vac_apply_"))
async def process_vacancy_selection(callback: Message, state: FSMContext) -> None:
    # Example callback_data: vac_apply_1
    from database import get_active_vacancies
    vacancies = await get_active_vacancies()
    vacancy_id = int(callback.data.split("_")[2])
    vacancy_title = next((v['title'] for v in vacancies if v['id'] == vacancy_id), "Noma'lum vakansiya")
    
    await state.update_data(vacancy_title=vacancy_title)
    await state.set_state(RecruitingForm.full_name)
    
    await callback.message.answer(
        f"✅ Tanlangan vakansiya: <b>{vacancy_title}</b>\n\n"
        "1/4. Ism va familiyangizni to'liq kiriting (masalan: Toshmatov Eshmat):",
        reply_markup=cancel_only_kb()
    )
    await callback.message.delete()
    await callback.answer()


@router.message(RecruitingForm.full_name, F.text.len() >= 4)
async def process_full_name(message: Message, state: FSMContext) -> None:
    full_name = message.text.strip()
    if not re.match(r"^[A-Za-zА-Яа-яЎўҚқҒғҲҳ' -]+$", full_name):
        await message.answer("Iltimos, ism-familiyani faqat harflardan foydalanib kiriting.")
        return

    await state.update_data(full_name=full_name)
    await state.set_state(RecruitingForm.phone)
    await message.answer(
        "2/4. Telefon raqamingizni yuboring (tugma orqali yoki qo'lda: +998901234567):",
        reply_markup=phone_request_kb(),
    )


@router.message(RecruitingForm.full_name)
async def process_full_name_invalid(message: Message) -> None:
    await message.answer("Ism-familiyani to'liq kiriting (kamida 4 belgi).")


# --- Step 2: Phone ---
@router.message(RecruitingForm.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.contact.phone_number)
    await ask_experience(message, state)


@router.message(RecruitingForm.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext) -> None:
    phone = normalize_phone(message.text)
    if not phone:
        await message.answer(
            "Raqam formati noto'g'ri. Namuna: +998901234567 yoki tugmadan foydalaning."
        )
        return
    await state.update_data(phone=phone)
    await ask_experience(message, state)


async def ask_experience(message: Message, state: FSMContext) -> None:
    await state.set_state(RecruitingForm.experience)
    await message.answer(
        "3/4. Ish tajribangiz va soha yo'nalishingiz haqida qisqacha yozing "
        "(masalan: 2 yil Python dasturchi):",
        reply_markup=cancel_only_kb(),
    )


# --- Step 3: Experience ---
@router.message(RecruitingForm.experience, F.text.len() >= 3)
async def process_experience(message: Message, state: FSMContext) -> None:
    await state.update_data(experience=message.text.strip())
    await state.set_state(RecruitingForm.resume)
    await message.answer(
        "4/4. Rezyumengizni yuboring (Fayl shaklida .pdf, .doc yoki .docx).\n\nAgar rezyumengiz bo'lmasa, quyidagi tugma orqali davom etishingiz mumkin.",
        reply_markup=resume_request_kb(),
    )


@router.message(RecruitingForm.experience)
async def process_experience_invalid(message: Message) -> None:
    await message.answer("Iltimos, tajribangiz haqida kamida bir necha so'z yozing.")


# --- Step 4: Resume or Skip / Generation ---
@router.message(RecruitingForm.resume)
async def process_resume(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.text == BTN_SKIP_RESUME:
        data = await state.get_data()
        await state.clear()
        candidate_id = await add_candidate(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=data["full_name"],
            phone=data["phone"],
            experience=data["experience"],
            resume_file_id="",
            resume_file_name="",
            vacancy_title=data.get("vacancy_title", "")
        )
        await message.answer("✅ Arizangiz (rezyumesiz) muvaffaqiyatli qabul qilindi. HR bo'limi siz bilan tez orada bog'lanadi.", reply_markup=main_menu_kb())
        admin_text = f"🔔 <b>Yangi ariza!</b>\n\n💼 Vakansiya: <b>{data.get('vacancy_title', '')}</b>\n👤 F.I.O: {data['full_name']}\n📞 Tel: {data['phone']}\n⏳ Tajriba: {data['experience']}\n👤 Username: @{message.from_user.username or '—'}\n📄 Rezyume: Yo'q"
        await bot.send_message(ADMIN_ID, admin_text)
        return
        
    if message.text == BTN_GENERATE_RESUME:
        await state.set_state(RecruitingForm.gen_photo)
        await message.answer("Iltimos, o'zingizning toza yuzli (yoki 3x4) rasmingizni yuboring:", reply_markup=cancel_only_kb())
        return

    if not message.document:
        await message.answer("Iltimos, fayl yuklang (PDF yoki DOCX).")
        return

    doc = message.document
    file_id = doc.file_id
    file_name = doc.file_name or ""
    data = await state.get_data()
    await state.clear()
    
    candidate_id = await add_candidate(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data["full_name"],
        phone=data["phone"],
        experience=data["experience"],
        resume_file_id=file_id,
        resume_file_name=file_name,
        vacancy_title=data.get("vacancy_title", "")
    )
    await message.answer("✅ Arizangiz muvaffaqiyatli qabul qilindi. HR bo'limi siz bilan tez orada bog'lanadi.", reply_markup=main_menu_kb())
    admin_text = f"🔔 <b>Yangi ariza!</b>\n\n💼 Vakansiya: <b>{data.get('vacancy_title', '')}</b>\n👤 F.I.O: {data['full_name']}\n📞 Tel: {data['phone']}\n⏳ Tajriba: {data['experience']}\n👤 Username: @{message.from_user.username or '—'}"
    await bot.send_document(ADMIN_ID, document=file_id, caption=admin_text)


# --- Resume Generator States ---
@router.message(RecruitingForm.gen_photo, F.photo)
async def process_gen_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    
    os.makedirs("temp_photos", exist_ok=True)
    photo_path = f"temp_photos/{photo.file_id}.jpg"
    await bot.download_file(file.file_path, photo_path)
    
    await state.update_data(photo_path=photo_path)
    await state.set_state(RecruitingForm.gen_birth_year)
    await message.answer("Tug'ilgan yilingizni kiriting (masalan, 1995):", reply_markup=cancel_only_kb())

@router.message(RecruitingForm.gen_photo)
async def process_gen_photo_invalid(message: Message) -> None:
    await message.answer("Iltimos, rasm yuklang.")

@router.message(RecruitingForm.gen_birth_year)
async def process_gen_birth_year(message: Message, state: FSMContext) -> None:
    await state.update_data(birth_year=message.text)
    await state.set_state(RecruitingForm.gen_address)
    await message.answer("Yashash manzilingizni kiriting (masalan, Toshkent sh., Chilonzor):", reply_markup=cancel_only_kb())

@router.message(RecruitingForm.gen_address)
async def process_gen_address(message: Message, state: FSMContext) -> None:
    await state.update_data(address=message.text)
    await state.set_state(RecruitingForm.gen_education)
    await message.answer("Ta'lim darajangizni kiriting (Oliy, o'rta maxsus...):", reply_markup=cancel_only_kb())

@router.message(RecruitingForm.gen_education)
async def process_gen_education(message: Message, state: FSMContext) -> None:
    await state.update_data(education=message.text)
    await state.set_state(RecruitingForm.gen_languages)
    await message.answer("Qaysi tillarni bilasiz (masalan, O'zbek, Rus, Ingliz):", reply_markup=cancel_only_kb())

@router.message(RecruitingForm.gen_languages)
async def process_gen_languages(message: Message, state: FSMContext) -> None:
    await state.update_data(languages=message.text)
    await state.set_state(RecruitingForm.gen_previous_work)
    await message.answer("Oldin qayerda ishlagansiz? (Kompaniya nomi va lavozimingiz, agar tajribangiz bo'lmasa 'Yo'q' deb yozing):", reply_markup=cancel_only_kb())

@router.message(RecruitingForm.gen_previous_work)
async def process_gen_previous_work(message: Message, state: FSMContext) -> None:
    await state.update_data(previous_work=message.text)
    await state.set_state(RecruitingForm.gen_skills)
    await message.answer("Qo'shimcha qobiliyatlaringiz, dasturlar bilimi (Word, Excel, Dasturlash...):", reply_markup=cancel_only_kb())

@router.message(RecruitingForm.gen_skills)
async def process_gen_skills(message: Message, state: FSMContext) -> None:
    await state.update_data(skills=message.text)
    await state.set_state(RecruitingForm.gen_expected_salary)
    await message.answer("Kutilayotgan oylik maoshingiz qancha? (masalan, 5 000 000 so'm yoki $500):", reply_markup=cancel_only_kb())

@router.message(RecruitingForm.gen_expected_salary)
async def process_gen_expected_salary(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.update_data(expected_salary=message.text)
    data = await state.get_data()
    
    import uuid
    from aiogram.types import FSInputFile
    from resume_generator import generate_pdf_resume
    
    os.makedirs("resumes", exist_ok=True)
    pdf_path = f"resumes/{uuid.uuid4()}.pdf"
    generate_pdf_resume(data, pdf_path)
    
    msg = await message.answer_document(
        FSInputFile(pdf_path),
        caption="📄 Sizning rezyumeyingiz yaratildi va HR bo'limiga yuborildi!",
        reply_markup=main_menu_kb()
    )
    file_id = msg.document.file_id
    
    # Cleanup files
    try:
        os.remove(pdf_path)
        if data.get('photo_path'):
            os.remove(data['photo_path'])
    except:
        pass
        
    await state.clear()
    
    candidate_id = await add_candidate(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data["full_name"],
        phone=data["phone"],
        experience=data["experience"],
        resume_file_id=file_id,
        resume_file_name="resume.pdf",
        vacancy_title=data.get("vacancy_title", "")
    )
    
    admin_text = f"🔔 <b>Yangi ariza (Bot orqali yaratilgan CV)!</b>\n\n💼 Vakansiya: <b>{data.get('vacancy_title', '')}</b>\n👤 F.I.O: {data['full_name']}\n📞 Tel: {data['phone']}\n⏳ Tajriba: {data['experience']}\n👤 Username: @{message.from_user.username or '—'}"
    await bot.send_document(ADMIN_ID, document=file_id, caption=admin_text)
