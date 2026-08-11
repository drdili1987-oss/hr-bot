from aiogram.fsm.state import State, StatesGroup


class RecruitingForm(StatesGroup):
    vacancy_id = State()
    custom_vacancy = State()
    full_name = State()
    phone = State()
    experience = State()
    resume = State()
    
    # Resume generator states
    gen_photo = State()
    gen_birth_year = State()
    gen_address = State()
    gen_education = State()
    gen_languages = State()
    gen_previous_work = State()
    gen_skills = State()
    gen_expected_salary = State()


class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()
    waiting_for_vacancy_title = State()
    waiting_for_vacancy_desc = State()
