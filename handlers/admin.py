import csv
import io

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

from config import ADMIN_ID
from database import create_vacancy, delete_vacancy, get_active_vacancies, get_all_candidates, get_candidates_count
from keyboards import (
    BTN_ADMIN_ADD_VACANCY,
    BTN_ADMIN_BROADCAST,
    BTN_ADMIN_DEL_VACANCY,
    BTN_ADMIN_EXPORT,
    BTN_ADMIN_STATS,
    BTN_ADMIN_VIEW_APPS,
    BTN_CANCEL,
    BTN_APPLY,
    BTN_ABOUT,
    BTN_OPEN_CANDIDACY,
    admin_menu_kb,
    cancel_only_kb,
    main_menu_kb,
    vacancies_inline_kb,
    candidate_pagination_kb,
    admin_vacancy_filter_kb,
)
from states import AdminStates

router = Router(name="admin")

# Filter to restrict router only for admin
router.message.filter(F.from_user.id == ADMIN_ID)


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "👨‍💻 <b>Admin paneliga xush kelibsiz!</b>\n\nQuyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=admin_menu_kb()
    )


@router.message(F.text == BTN_ADMIN_STATS)
async def admin_stats(message: Message) -> None:
    count = await get_candidates_count()
    await message.answer(f"📊 <b>Statistika</b>\n\nJami kelib tushgan arizalar soni: <b>{count} ta</b>")


# --- View Applications ---
async def send_candidate_view(message_or_callback: Message | CallbackQuery, index: int, filter_val: str = "all", edit: bool = False):
    from database import get_candidates_by_vacancy, get_active_vacancies, search_candidates
    
    if filter_val == "all":
        candidates = await get_all_candidates()
    elif filter_val.startswith("search:"):
        query = filter_val.split(":", 1)[1]
        candidates = await search_candidates(query)
    else:
        vacancies = await get_active_vacancies()
        vacancy_id = int(filter_val)
        vacancy_title = next((v['title'] for v in vacancies if v['id'] == vacancy_id), "Noma'lum")
        candidates = await get_candidates_by_vacancy(vacancy_title)
        
    if not candidates:
        text = "Ushbu bo'limda hech qanday ariza yo'q."
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text)
        else:
            await message_or_callback.message.edit_text(text)
        return
        
    total_count = len(candidates)
    if index >= total_count:
        index = total_count - 1
    if index < 0:
        index = 0
        
    cand = candidates[index]
    
    # Generate text
    vacancy_title = cand['vacancy_title'] if 'vacancy_title' in cand.keys() and cand['vacancy_title'] else "Noma'lum"
    text = (
        f"📄 <b>Ariza {index + 1}/{total_count}</b>\n\n"
        f"🆔 ID: {cand['id']}\n"
        f"💼 Vakansiya: <b>{vacancy_title}</b>\n"
        f"👤 F.I.O: {cand['full_name']}\n"
        f"📞 Tel: {cand['phone']}\n"
        f"⏳ Tajriba: {cand['experience']}\n"
        f"📅 Sana: {cand['created_at']}\n"
        f"👤 Username: @{cand['username'] or '—'}"
    )
    
    kb = candidate_pagination_kb(index, total_count, filter_val)
    has_resume = bool(cand['resume_file_id'])
    
    if isinstance(message_or_callback, Message):
        if has_resume:
            await message_or_callback.answer_document(cand['resume_file_id'], caption=text, reply_markup=kb)
        else:
            text += "\n\n<i>❗️ Rezyume taqdim etilmagan</i>"
            await message_or_callback.answer(text, reply_markup=kb)
    else:
        # Edit existing message
        msg = message_or_callback.message
        await msg.delete()
        if has_resume:
            await message_or_callback.message.answer_document(cand['resume_file_id'], caption=text, reply_markup=kb)
        else:
            text += "\n\n<i>❗️ Rezyume taqdim etilmagan</i>"
            await message_or_callback.message.answer(text, reply_markup=kb)


@router.message(F.text == BTN_ADMIN_VIEW_APPS)
async def admin_view_apps(message: Message) -> None:
    from database import get_active_vacancies
    vacancies = await get_active_vacancies()
    
    if not vacancies:
        await message.answer(
            "Bazada ochiq vakansiyalar yo'q. Barcha arizalarni ko'rish:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Barcha arizalar", callback_data="filter_vac_all")]
            ])
        )
        return
        
    await message.answer(
        "📂 Qaysi vakansiya bo'yicha arizalarni ko'rmoqchisiz?",
        reply_markup=admin_vacancy_filter_kb(vacancies)
    )


@router.callback_query(F.data.startswith("filter_vac_"))
async def process_admin_vacancy_filter(callback: CallbackQuery) -> None:
    filter_val = callback.data.split("_")[2] # "all" or id
    await send_candidate_view(callback, 0, filter_val)
    await callback.answer()


@router.callback_query(F.data.startswith("cand_prev_"))
async def admin_view_apps_prev(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    index = int(parts[2])
    filter_val = parts[3] if len(parts) > 3 else "all"
    await send_candidate_view(callback, index, filter_val)
    await callback.answer()


@router.callback_query(F.data.startswith("cand_next_"))
async def admin_view_apps_next(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    index = int(parts[2])
    filter_val = parts[3] if len(parts) > 3 else "all"
    await send_candidate_view(callback, index, filter_val)
    await callback.answer()


@router.message(F.text == BTN_ADMIN_EXPORT)
async def admin_export(message: Message) -> None:
    candidates = await get_all_candidates()
    if not candidates:
        await message.answer("Bazada hech qanday nomzod yo'q.")
        return
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Telegram ID', 'Username', 'F.I.O', 'Telefon', 'Tajriba', 'Sana'])
    
    for row in candidates:
        writer.writerow([
            row['id'], row['telegram_id'], row['username'] or '',
            row['full_name'], row['phone'], row['experience'], row['created_at']
        ])
        
    csv_bytes = output.getvalue().encode('utf-8')
    csv_file = BufferedInputFile(csv_bytes, filename="nomzodlar.csv")
    
    await message.answer_document(
        document=csv_file,
        caption="📥 Barcha nomzodlar ro'yxati (CSV formatida)"
    )


@router.message(F.text == BTN_ADMIN_BROADCAST)
async def admin_broadcast_start(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_for_broadcast_message)
    await message.answer(
        "✉️ <b>Xabar tarqatish</b>\n\nBarcha ariza topshirgan nomzodlarga yubormoqchi bo'lgan xabaringizni kiriting:",
        reply_markup=cancel_only_kb()
    )


@router.message(AdminStates.waiting_for_broadcast_message, F.text == BTN_CANCEL)
async def cancel_broadcast(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Xabar tarqatish bekor qilindi.", reply_markup=admin_menu_kb())


@router.message(AdminStates.waiting_for_broadcast_message)
async def process_broadcast(message: Message, state: FSMContext) -> None:
    candidates = await get_all_candidates()
    if not candidates:
        await message.answer("Bazada hech qanday nomzod yo'q.", reply_markup=admin_menu_kb())
        await state.clear()
        return

    # To avoid sending multiple messages to the same user if they applied multiple times
    unique_user_ids = set([row['telegram_id'] for row in candidates])
    
    success = 0
    fail = 0
    
    msg = await message.answer(f"Xabar {len(unique_user_ids)} ta foydalanuvchiga yuborilmoqda, kuting...")
    
    for user_id in unique_user_ids:
        try:
            await message.copy_to(chat_id=user_id)
            success += 1
        except Exception:
            fail += 1
            
    await state.clear()
    await msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"Muvaffaqiyatli: {success} ta\n"
        f"Yuborilmadi: {fail} ta (botni bloklagan bo'lishi mumkin)"
    )
    await message.answer("Bosh menyu:", reply_markup=admin_menu_kb())


# --- Add Vacancy ---
@router.message(F.text == BTN_ADMIN_ADD_VACANCY)
async def admin_add_vacancy_start(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_for_vacancy_title)
    await message.answer(
        "➕ <b>Vakansiya qo'shish</b>\n\nYangi vakansiya nomini kiriting (masalan: Python Dasturchi):",
        reply_markup=cancel_only_kb()
    )


@router.message(AdminStates.waiting_for_vacancy_title, F.text == BTN_CANCEL)
@router.message(AdminStates.waiting_for_vacancy_desc, F.text == BTN_CANCEL)
async def cancel_vacancy(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Vakansiya qo'shish bekor qilindi.", reply_markup=admin_menu_kb())


@router.message(AdminStates.waiting_for_vacancy_title)
async def admin_add_vacancy_title(message: Message, state: FSMContext) -> None:
    await state.update_data(vacancy_title=message.text.strip())
    await state.set_state(AdminStates.waiting_for_vacancy_desc)
    await message.answer(
        "Vakansiya haqida qisqacha ma'lumot (talablar, oylik) kiriting:",
        reply_markup=cancel_only_kb()
    )


@router.message(AdminStates.waiting_for_vacancy_desc)
async def admin_add_vacancy_desc(message: Message, state: FSMContext) -> None:
    desc = message.text.strip()
    data = await state.get_data()
    title = data['vacancy_title']
    
    await create_vacancy(title=title, description=desc)
    await state.clear()
    
    await message.answer(
        f"✅ <b>Yangi vakansiya yaratildi!</b>\n\nNomi: {title}\nMa'lumot: {desc}",
        reply_markup=admin_menu_kb()
    )


# --- Delete Vacancy ---
@router.message(F.text == BTN_ADMIN_DEL_VACANCY)
async def admin_del_vacancy_list(message: Message) -> None:
    vacancies = await get_active_vacancies()
    if not vacancies:
        await message.answer("O'chirish uchun ochiq vakansiyalar yo'q.")
        return
        
    await message.answer(
        "🗑 Qaysi vakansiyani o'chirmoqchisiz? Tanlang:",
        reply_markup=vacancies_inline_kb(vacancies, action="del")
    )


@router.callback_query(F.data.startswith("vac_del_"))
async def admin_del_vacancy_confirm(callback: CallbackQuery) -> None:
    vacancy_id = int(callback.data.split("_")[2])
    await delete_vacancy(vacancy_id)
    await callback.message.edit_text("✅ Vakansiya muvaffaqiyatli o'chirildi (yopildi).")
    await callback.answer()


# --- Search Handling ---
@router.message(F.text)
async def admin_text_search(message: Message, state: FSMContext) -> None:
    # Ignore commands and known keyboard buttons
    if message.text.startswith("/") or message.text in [
        BTN_CANCEL, BTN_APPLY, BTN_ABOUT, BTN_OPEN_CANDIDACY,
        BTN_ADMIN_STATS, BTN_ADMIN_EXPORT, BTN_ADMIN_BROADCAST,
        BTN_ADMIN_ADD_VACANCY, BTN_ADMIN_DEL_VACANCY, BTN_ADMIN_VIEW_APPS
    ]:
        return

    # If state is active, it means admin is doing something else (like adding a vacancy).
    # We only search if state is clear.
    current_state = await state.get_state()
    if current_state is None:
        query = message.text.strip()
        if len(query) < 2:
            return
        
        await message.answer(f"🔍 <b>Qidiruv natijalari:</b> <i>{query}</i>")
        await send_candidate_view(message, 0, f"search:{query}")

