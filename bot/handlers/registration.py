import json

from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.database.database import async_session
from bot.database.models import User
from bot.keyboards.inline import (
    get_add_more_keyboard,
    get_current_job_keyboard,
    get_degree_keyboard,
    get_has_license_keyboard,
    get_is_studying_keyboard,
    get_language_level_keyboard,
    get_license_category_keyboard,
    get_skip_keyboard,
    get_start_education_keyboard,
    get_start_experience_keyboard,
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.states.cv_states import Registration

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Привіт,\n\n"
        "Я твій ШІ-асистент для генерації резюме. "
        "Давай зберемо базову інформацію.\n\n"
        "Напиши своє ім'я:"
    )
    await state.set_state(Registration.waiting_for_first_name)

@router.message(Registration.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Відмінно. Тепер напиши своє прізвище:")
    await state.set_state(Registration.waiting_for_last_name)

@router.message(Registration.waiting_for_last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer("Введи свій E-mail:")
    await state.set_state(Registration.waiting_for_email)

@router.message(Registration.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Введи номер телефону:")
    await state.set_state(Registration.waiting_for_phone)

@router.message(Registration.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("В якій країні ти знаходишся:")
    await state.set_state(Registration.waiting_for_country)

@router.message(Registration.waiting_for_country)
async def process_country(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text)
    await message.answer("Введи своє місто:")
    await state.set_state(Registration.waiting_for_city)

@router.message(Registration.waiting_for_city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer(
        "Супер! Тепер надішли фотографію для резюме.\n\n"
        "📸 Найкраще підійде портретне фото на світлому фоні (як на паспорт). "
        "Просто відправ зображення сюди:"
    )
    await state.set_state(Registration.waiting_for_photo)


@router.message(Registration.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_file_id)

    data = await state.get_data()
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        profile_json = json.dumps(data, ensure_ascii=False)
        if user:
            user.profile_data = profile_json
        else:
            user = User(
                telegram_id=message.from_user.id,
                profile_data=profile_json,
            )
            session.add(user)
        await session.commit()

    if data.get("is_editing"):
        await message.answer(
            "✅ Базову інформацію та фото оновлено!",
            reply_markup=get_main_menu_keyboard(),
        )
        await state.clear()
    else:
        await message.answer(
            "✅ Базовий профіль та фото збережено!\n\n"
            "Тепер перейдемо до досвіду роботи."
        )
        await state.set_state(Registration.waiting_for_experience)
        await start_experience(message, state)


@router.message(Registration.waiting_for_experience)
async def start_experience(message: types.Message, state: FSMContext):
    await state.update_data(experience_list=[])
    await message.answer(
        "Чи маєш ти досвід роботи?",
        reply_markup=get_start_experience_keyboard(),
    )
    await state.set_state(Registration.exp_initial_decision)


@router.callback_query(
    Registration.exp_initial_decision,
    lambda c: c.data in ["exp_add_yes", "exp_add_no"],
)
async def process_exp_initial_decision(callback: CallbackQuery, state: FSMContext):
    if callback.data == "exp_add_no":
        await callback.message.edit_text(
            callback.message.text + "\n\n*Вибрано:* Немає досвіду"
        )
        await save_to_db_and_continue(
            callback,
            state,
            "experience",
            "experience_list",
            "Переходимо до освіти 🎓\n\nВведи назву навчального закладу:",
            Registration.waiting_for_education,
        )
        await start_education(callback.message, state)
    else:
        await callback.message.edit_text(
            callback.message.text + "\n\n*Вибрано:* Додати досвід"
        )
        await callback.message.answer(
            "Введи назву посади (наприклад: Python Developer):"
        )
        await state.set_state(Registration.exp_title)

@router.message(Registration.exp_title)
async def process_exp_title(message: types.Message, state: FSMContext):
    await state.update_data(current_exp_title=message.text)
    await message.answer("В якій компанії ти працював/ла?")
    await state.set_state(Registration.exp_company)

@router.message(Registration.exp_company)
async def process_exp_company(message: types.Message, state: FSMContext):
    await state.update_data(current_exp_company=message.text)
    await message.answer("Коли ти почав/ла там працювати? (формат: ММ.РРРР, наприклад 09.2024):")
    await state.set_state(Registration.exp_start)

@router.message(Registration.exp_start)
async def process_exp_start(message: types.Message, state: FSMContext):
    await state.update_data(current_exp_start=message.text)
    await message.answer(
        "Ти працюєш там зараз?",
        reply_markup=get_current_job_keyboard()
    )
    # Ждем нажатия на инлайн-кнопку
    await state.set_state(Registration.exp_end)

@router.callback_query(Registration.exp_end, lambda c: c.data in ["job_current_yes", "job_current_no"])
async def process_exp_current(callback: CallbackQuery, state: FSMContext):
    if callback.data == "job_current_yes":
        await callback.message.edit_text(f"{callback.message.text}\n\n*Вибрано: Так, працюю зараз*")
        await save_experience_entry(callback.message, state, end_date=None, is_current=True)
    else:
        await callback.message.edit_text(f"{callback.message.text}\n\n*Вибрано: Ні, вже не працюю*")
        await callback.message.answer("Коли ти закінчив/ла там працювати? (формат: ММ.РРРР):")
        # Остаемся в state exp_end, но теперь ждем текстовое сообщение с датой

@router.message(Registration.exp_end)
async def process_exp_end_date(message: types.Message, state: FSMContext):
    await save_experience_entry(message, state, end_date=message.text, is_current=False)

async def save_experience_entry(message: types.Message, state: FSMContext, end_date: str | None, is_current: bool):
    data = await state.get_data()
    
    # Формируем словарь одного места работы
    exp_entry = {
        "title": data.get("current_exp_title"),
        "company": data.get("current_exp_company"),
        "start_date": data.get("current_exp_start"),
        "end_date": end_date,
        "is_current": is_current
    }
    
    # Добавляем в общий список
    experience_list = data.get("experience_list", [])
    experience_list.append(exp_entry)
    await state.update_data(experience_list=experience_list)
    
    await message.answer(
        f"✅ Додано: {exp_entry['title']} в {exp_entry['company']}\n\n"
        "Бажаєш додати ще одне місце роботи?",
        reply_markup=get_add_more_keyboard("exp")
    )
    await state.set_state(Registration.exp_decision)

@router.callback_query(Registration.exp_decision, lambda c: c.data.startswith("add_more_") or c.data.startswith("continue_"))
async def process_exp_decision(callback: CallbackQuery, state: FSMContext):
    # Убираем кнопки у предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if callback.data.startswith("add_more"):
        await callback.message.answer("Введи назву наступної посади:")
        await state.set_state(Registration.exp_title)
    else:
        await save_to_db_and_continue(
            callback,
            state,
            "experience",
            "experience_list",
            "Відмінно, досвід роботи збережено! Переходимо до освіти.",
            Registration.waiting_for_education,
        )
        await start_education(callback.message, state)

# --- Початок блоку Освіти ---

@router.message(Registration.waiting_for_education)
async def start_education(message: types.Message, state: FSMContext):
    await state.update_data(education_list=[])
    await message.answer("Чи маєш ти освіту (університет, коледж, курси)?", reply_markup=get_start_education_keyboard())
    await state.set_state(Registration.edu_initial_decision)

@router.callback_query(Registration.edu_initial_decision, lambda c: c.data in ["edu_add_yes", "edu_add_no"])
async def process_edu_initial_decision(callback: CallbackQuery, state: FSMContext):
    if callback.data == "edu_add_no":
        await callback.message.edit_text(callback.message.text + "\n\n*Вибрано:* Немає освіти")
        await save_to_db_and_continue(callback, state, "education", "education_list", 
                                      "Освіту пропущено. 🎓\n\nДавай додамо мови. Напиши мову (наприклад, English):", 
                                      Registration.lang_name)
    else:
        await callback.message.edit_text(callback.message.text + "\n\n*Вибрано:* Додати освіту")
        await callback.message.answer("Введи назву навчального закладу (наприклад, Technical University of Kosice):")
        await state.set_state(Registration.edu_inst)

@router.message(Registration.edu_inst)
async def process_edu_inst(message: types.Message, state: FSMContext):
    await state.update_data(current_edu_inst=message.text)
    await message.answer("Який ступінь ти здобув/здобуваєш?", reply_markup=get_degree_keyboard())
    await state.set_state(Registration.edu_degree)

@router.callback_query(Registration.edu_degree, lambda c: c.data.startswith("deg_"))
async def process_edu_degree_cb(callback: CallbackQuery, state: FSMContext):
    if callback.data == "deg_Other":
        await callback.message.edit_text("Напиши свій ступінь текстом:")
    else:
        degree_map = {
            "deg_Bachelor": "Bachelor's Degree", "deg_Master": "Master's Degree",
            "deg_Assoc": "Assoc. Degree / Diploma", "deg_High": "High School"
        }
        deg = degree_map[callback.data]
        await callback.message.edit_text(f"Ступінь: {deg}")
        await state.update_data(current_edu_degree=deg)
        await callback.message.answer("Яка спеціальність? (наприклад, Information Science):")
        await state.set_state(Registration.edu_field)

@router.message(Registration.edu_degree)
async def process_edu_degree_msg(message: types.Message, state: FSMContext):
    await state.update_data(current_edu_degree=message.text)
    await message.answer("Яка спеціальність? (наприклад, Information Science):")
    await state.set_state(Registration.edu_field)

@router.message(Registration.edu_field)
async def process_edu_field(message: types.Message, state: FSMContext):
    await state.update_data(current_edu_field=message.text)
    await message.answer("Рік початку навчання (наприклад, 2023):")
    await state.set_state(Registration.edu_start)

@router.message(Registration.edu_start)
async def process_edu_start(message: types.Message, state: FSMContext):
    await state.update_data(current_edu_start=message.text)
    await message.answer("Який зараз статус навчання?", reply_markup=get_is_studying_keyboard())
    await state.set_state(Registration.edu_is_studying)

@router.callback_query(Registration.edu_is_studying, lambda c: c.data in ["edu_studying_yes", "edu_studying_no"])
async def process_edu_studying(callback: CallbackQuery, state: FSMContext):
    await state.update_data(current_edu_studying=(callback.data == "edu_studying_yes"))
    await callback.message.edit_text(callback.message.text + "\n\n*Вибрано:* " + ("Ще вчуся" if callback.data == "edu_studying_yes" else "Вже закінчив/ла"))
    
    if callback.data == "edu_studying_yes":
        await callback.message.answer("Введи очікуваний рік закінчення (наприклад, 2026):")
    else:
        await callback.message.answer("Введи рік закінчення:")
    await state.set_state(Registration.edu_end_year)

@router.message(Registration.edu_end_year)
async def process_edu_end(message: types.Message, state: FSMContext):
    data = await state.get_data()
    edu_entry = {
        "institution": data.get("current_edu_inst"),
        "degree": data.get("current_edu_degree"),
        "field_of_study": data.get("current_edu_field"),
        "start_year": data.get("current_edu_start"),
        "end_year": message.text,
        "is_studying": data.get("current_edu_studying"),
        "gpa": "NA"
    }
    
    edu_list = data.get("education_list", [])
    edu_list.append(edu_entry)
    await state.update_data(education_list=edu_list)
    
    await message.answer(f"✅ Додано освіту: {edu_entry['institution']}\n\nБажаєш додати ще один навчальний заклад?", reply_markup=get_add_more_keyboard("edu"))
    await state.set_state(Registration.edu_decision)

@router.callback_query(Registration.edu_decision, lambda c: c.data.startswith("add_more_edu") or c.data.startswith("continue_edu"))
async def process_edu_decision(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if callback.data.startswith("add_more"):
        await callback.message.answer("Введи назву наступного навчального закладу:")
        await state.set_state(Registration.edu_inst)
    else:
        await save_to_db_and_continue(callback, state, "education", "education_list", 
                                      "Освіту збережено! 🎓\n\nДавай додамо мови. Напиши мову (наприклад, English):", 
                                      Registration.lang_name)

# --- Початок блоку Мов ---

@router.message(Registration.lang_name)
async def process_lang_name(message: types.Message, state: FSMContext):
    await state.update_data(current_lang_name=message.text)
    await message.answer("Обери рівень володіння:", reply_markup=get_language_level_keyboard())
    await state.set_state(Registration.lang_level)

@router.callback_query(Registration.lang_level, lambda c: c.data.startswith("lang_lvl_"))
async def process_lang_level(callback: CallbackQuery, state: FSMContext):
    level = callback.data.split("_")[2] # Отримуємо A1, B2 і т.д.
    await callback.message.edit_text(f"{callback.message.text}\n\n*Вибрано:* {level}")
    
    data = await state.get_data()
    lang_entry = {"name": data.get("current_lang_name"), "level": level}
    
    lang_list = data.get("languages_list", [])
    lang_list.append(lang_entry)
    await state.update_data(languages_list=lang_list)
    
    await callback.message.answer(f"✅ Додано мову: {lang_entry['name']} ({lang_entry['level']})\n\nДодати ще одну мову?", reply_markup=get_add_more_keyboard("lang"))
    await state.set_state(Registration.lang_decision)

@router.callback_query(Registration.lang_decision, lambda c: c.data.startswith("add_more_lang") or c.data.startswith("continue_lang"))
async def process_lang_decision(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if callback.data.startswith("add_more"):
        await callback.message.answer("Напиши наступну мову:")
        await state.set_state(Registration.lang_name)
    else:
        await save_to_db_and_continue(callback, state, "languages", "languages_list", 
                                      "Мови збережено! 🗣\n\nТепер напиши свої ключові навички через кому (наприклад: Python, Flask, SQL, React, Git):", 
                                      Registration.skills_input)

# --- Навички, Права, Проєкти ---

@router.message(Registration.skills_input)
async def process_skills(message: types.Message, state: FSMContext):
    skills = [skill.strip() for skill in message.text.split(",")]
    await state.update_data(skills_list=skills)

    await save_to_db_and_continue(
        message,
        state,
        "skills",
        "skills_list",
        "Чи маєш ти водійське посвідчення?",
        Registration.waiting_for_driving_license,
        reply_markup=get_has_license_keyboard(),
        is_chain=True,
    )


@router.callback_query(
    Registration.waiting_for_driving_license,
    lambda c: c.data.startswith("has_license_"),
)
async def process_has_driving_license(callback: CallbackQuery, state: FSMContext):
    if callback.data == "has_license_yes":
        await callback.message.edit_text(
            callback.message.text + "\n\n*Вибрано:* Так, є"
        )
        await callback.message.answer(
            "Обери категорію (або напиши текстом):",
            reply_markup=get_license_category_keyboard(),
        )
        await state.set_state(Registration.driving_license_category)
    else:
        await callback.message.edit_text(
            callback.message.text + "\n\n*Вибрано:* Немає"
        )
        await state.update_data(driving_license="Немає")
        await save_to_db_and_continue(
            callback,
            state,
            "driving_license",
            "driving_license",
            "Бажаєш додати посилання на свій LinkedIn? Надішли посилання або натисни кнопку, щоб пропустити.",
            Registration.waiting_for_linkedin,
            reply_markup=get_skip_keyboard("skip_linkedin"),
            is_chain=True,
        )


@router.callback_query(
    Registration.driving_license_category,
    lambda c: c.data.startswith("lic_cat_"),
)
async def process_driving_license_category_cb(
    callback: CallbackQuery, state: FSMContext
):
    if callback.data == "lic_cat_other":
        await callback.message.edit_text(
            "Напиши свою категорію прав (наприклад, T, C1E):"
        )
    else:
        category = callback.data.split("_")[2]
        await callback.message.edit_text(
            f"Водійське посвідчення: Категорія {category}"
        )
        await state.update_data(driving_license=f"Категорія {category}")
        await save_to_db_and_continue(
            callback,
            state,
            "driving_license",
            "driving_license",
            "Бажаєш додати посилання на свій LinkedIn? Надішли посилання або натисни кнопку, щоб пропустити.",
            Registration.waiting_for_linkedin,
            reply_markup=get_skip_keyboard("skip_linkedin"),
            is_chain=True,
        )


@router.message(Registration.driving_license_category)
async def process_driving_license_category_msg(
    message: types.Message, state: FSMContext
):
    await state.update_data(driving_license=f"Категорія {message.text}")
    await save_to_db_and_continue(
        message,
        state,
        "driving_license",
        "driving_license",
        "Бажаєш додати посилання на свій LinkedIn? Надішли посилання або натисни кнопку, щоб пропустити.",
        Registration.waiting_for_linkedin,
        reply_markup=get_skip_keyboard("skip_linkedin"),
        is_chain=True,
    )

# --- LinkedIn та GitHub ---

@router.callback_query(Registration.waiting_for_linkedin, F.data == "skip_linkedin")
async def skip_linkedin(callback: CallbackQuery, state: FSMContext):
    await state.update_data(linkedin="Немає")
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    if data.get("editing_link") == "linkedin":
        await save_profile_field(callback, state, "linkedin", "Немає")
        return
    await ask_github(callback.message, state)


@router.message(Registration.waiting_for_linkedin)
async def process_linkedin(message: types.Message, state: FSMContext):
    await state.update_data(linkedin=message.text)
    data = await state.get_data()
    if data.get("editing_link") == "linkedin":
        await save_profile_field(message, state, "linkedin", message.text)
        return
    await ask_github(message, state)


async def ask_github(message: types.Message, state: FSMContext):
    await message.answer(
        "Бажаєш додати посилання на GitHub? Надішли посилання або натисни кнопку, щоб пропустити.",
        reply_markup=get_skip_keyboard("skip_github"),
    )
    await state.set_state(Registration.waiting_for_github)


@router.callback_query(Registration.waiting_for_github, F.data == "skip_github")
async def skip_github(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    if data.get("editing_link") == "github":
        await save_profile_field(callback, state, "github", "Немає")
        return
    await state.update_data(github="Немає")
    await ask_projects(callback.message, state)


@router.message(Registration.waiting_for_github)
async def process_github(message: types.Message, state: FSMContext):
    await state.update_data(github=message.text)
    data = await state.get_data()
    if data.get("editing_link") == "github":
        await save_profile_field(message, state, "github", message.text)
        return
    await ask_projects(message, state)


async def ask_projects(message: types.Message, state: FSMContext):
    await message.answer(
        "Останній крок! Опиши свій загальний досвід або власні/навчальні проєкти.",
        reply_markup=get_skip_keyboard("skip_projects"),
    )
    await state.set_state(Registration.waiting_for_projects)


@router.callback_query(Registration.waiting_for_projects, lambda c: c.data == "skip_projects")
async def skip_projects(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.update_data(projects="Не вказано")
    await finish_registration(callback, state)

@router.message(Registration.waiting_for_projects)
async def process_projects(message: types.Message, state: FSMContext):
    await state.update_data(projects=message.text)
    await finish_registration(message, state)


# --- Допоміжні функції для роботи з БД ---

async def save_to_db_and_continue(
    event,
    state: FSMContext,
    db_key: str,
    state_key: str,
    next_text: str,
    next_state,
    reply_markup=None,
    is_chain=False,
):
    """Універсальна функція для збереження блоку в БД і переходу далі"""
    data = await state.get_data()
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == event.from_user.id))
        user = result.scalar_one()
        current_profile = json.loads(user.profile_data)
        current_profile[db_key] = data.get(state_key)
        user.profile_data = json.dumps(current_profile, ensure_ascii=False)
        await session.commit()
    
    msg = event.message if isinstance(event, CallbackQuery) else event
    if data.get("is_editing") and not is_chain:
        await msg.answer(
            "✅ Інформацію успішно оновлено!",
            reply_markup=get_main_menu_keyboard(),
        )
        await state.clear()
    else:
        await msg.answer(next_text, reply_markup=reply_markup)
        await state.set_state(next_state)

async def finish_registration(event, state: FSMContext):
    """Фінал реєстрації або редагування"""
    data = await state.get_data()
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == event.from_user.id))
        user = result.scalar_one()
        current_profile = json.loads(user.profile_data)
        current_profile["projects"] = data.get("projects")
        current_profile["linkedin"] = data.get("linkedin", current_profile.get("linkedin", "Немає"))
        current_profile["github"] = data.get("github", current_profile.get("github", "Немає"))
        user.profile_data = json.dumps(current_profile, ensure_ascii=False)
        await session.commit()

    msg = event.message if isinstance(event, CallbackQuery) else event
    if data.get("is_editing"):
        await msg.answer(
            "✅ Розділ 'Навички та інше' успішно оновлено!",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await msg.answer(
            "🎉 Супер! Твій базовий профіль повністю заповнено та збережено.\n\n"
            "Скористайся меню нижче, щоб керувати профілем або згенерувати резюме.",
            reply_markup=get_main_menu_keyboard(),
        )
    await state.clear()


async def save_profile_field(event, state: FSMContext, field: str, value: str):
    """Зберігає окреме поле профілю під час редагування."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == event.from_user.id))
        user = result.scalar_one()
        profile = json.loads(user.profile_data)
        profile[field] = value
        user.profile_data = json.dumps(profile, ensure_ascii=False)
        await session.commit()

    message = event.message if isinstance(event, CallbackQuery) else event
    await message.answer("✅ Посилання оновлено.", reply_markup=get_main_menu_keyboard())
    await state.clear()