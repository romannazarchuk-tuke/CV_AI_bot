import json
import os

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from sqlalchemy import select

from bot.database.database import async_session
from bot.database.models import User
from bot.keyboards.inline import (
    get_cv_draft_keyboard,
    get_cv_language_keyboard,
    get_skip_keyboard,
)
from bot.services.llm_service import edit_cv_json, generate_cv_json
from bot.states.cv_states import VacancyProcessing

router = Router()

LICENSE_KEYWORDS = (
    "driver",
    "driving",
    "licence",
    "license",
    "řidič",
    "vodič",
    "права",
    "автомобіль",
)


def filter_driving_license(cv_data: dict, vacancy_text: str, additional_prompt: str) -> dict:
    """Удаляет права, если вакансия или пожелания их не требуют."""
    search_text = f"{vacancy_text} {additional_prompt}".casefold()
    if not any(keyword in search_text for keyword in LICENSE_KEYWORDS):
        cv_data["driving_license"] = ""
    return cv_data

@router.message(VacancyProcessing.waiting_for_vacancy_text)
async def process_vacancy_text(message: types.Message, state: FSMContext):
    # Тепер ми НАКОПИЧУЄМО текст, скільки б повідомлень Telegram не прислав
    data = await state.get_data()
    current_text = data.get("vacancy_text", "")
    new_text = current_text + "\n\n" + message.text if current_text else message.text
    
    await state.update_data(vacancy_text=new_text)
    # Нікуди не переходимо. Чекаємо, поки користувач натисне кнопку "Завершити"

@router.callback_query(VacancyProcessing.waiting_for_vacancy_text, F.data == "vacancy_finished")
async def finish_vacancy_input(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("vacancy_text"):
        await callback.answer("Ти ще не надіслав жодного тексту!", show_alert=True)
        return
        
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Отримав вакансію! 📝\n\n"
        "Якою мовою потрібно згенерувати резюме?",
        reply_markup=get_cv_language_keyboard()
    )
    await state.set_state(VacancyProcessing.waiting_for_cv_language)

@router.callback_query(VacancyProcessing.waiting_for_cv_language, F.data.startswith("lang_"))
async def process_cv_language(callback: types.CallbackQuery, state: FSMContext):
    chosen_lang = callback.data.split("_")[1]
    await state.update_data(cv_language=chosen_lang)
    
    await callback.message.edit_text(f"{callback.message.text}\n\n*Вибрано:* {chosen_lang}")
    await callback.message.answer(
        "Чи є у тебе додаткові побажання до промпту?\n"
        "(Наприклад: 'зроби акцент на досвіді з Python', 'прибери досвід роботи баристою' або 'напиши про права')\n\n"
        "Якщо ні — просто натисни кнопку.",
        reply_markup=get_skip_keyboard("skip_prompt")
    )
    await state.set_state(VacancyProcessing.waiting_for_additional_prompt)

@router.callback_query(VacancyProcessing.waiting_for_additional_prompt, F.data == "skip_prompt")
async def skip_additional_prompt(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(additional_prompt="Без додаткових побажань")
    await callback.message.edit_reply_markup(reply_markup=None)
    # Передаємо весь callback як подію
    await start_llm_generation(callback, state)

@router.message(VacancyProcessing.waiting_for_additional_prompt)
async def process_additional_prompt(message: types.Message, state: FSMContext):
    await state.update_data(additional_prompt=message.text)
    # Передаємо message як подію
    await start_llm_generation(message, state)

async def start_llm_generation(event, state: FSMContext):
    user_id = event.from_user.id
    msg = event.message if isinstance(event, types.CallbackQuery) else event
    
    data = await state.get_data()
    
    wait_msg = await msg.answer("⏳ Аналізую профіль та вакансію. Генерую чернетку резюме...")
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        
    if not user or not user.profile_data:
        await wait_msg.edit_text("❌ Помилка: Профіль не знайдено.")
        return
        
    profile_data = json.loads(user.profile_data)
    
    try:
        # Первинна генерація
        generated_json_str = await generate_cv_json(
            profile_data=profile_data,
            vacancy_text=data['vacancy_text'],
            language=data['cv_language'],
            extra_prompt=data['additional_prompt']
        )

        cv_data = json.loads(generated_json_str)
        cv_data = filter_driving_license(
            cv_data,
            data.get("vacancy_text", ""),
            data.get("additional_prompt", ""),
        )
        generated_json_str = json.dumps(cv_data, ensure_ascii=False)
        
        await state.update_data(generated_cv_json=generated_json_str, profile_data=profile_data)
        await wait_msg.delete()
        await show_cv_draft(msg, generated_json_str, state)
        
    except Exception as exc:  # noqa: BLE001 - boundary error is shown to the user
        await wait_msg.edit_text(f"❌ Помилка при генерації:\n{exc}")
        await state.clear()


async def show_cv_draft(message: types.Message, cv_json: str, state: FSMContext):
    """Виводить текстове прев'ю резюме з кнопками для правок."""
    cv = json.loads(cv_json)

    draft_text = "📝 **ЧЕРНЕТКА РЕЗЮМЕ**\n\n"
    draft_text += f"**Про мене:**\n{cv.get('summary', '')}\n\n"

    draft_text += "**Досвід роботи:**\n"
    for exp in cv.get('experience', []):
        draft_text += (
            f"▪️ {exp.get('title', '')} | {exp.get('company', '')}\n"
            f"{exp.get('description', '')}\n\n"
        )

    draft_text += f"**Навички:** {', '.join(cv.get('skills', []))}\n\n"
    draft_text += f"**Проєкти:** {cv.get('projects', '')}\n"

    await message.answer(
        text=f"{draft_text}\nОзнайомся з текстом. Якщо щось не подобається — вибери розділ для редагування.",
        reply_markup=get_cv_draft_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(VacancyProcessing.waiting_for_feedback)


@router.callback_query(VacancyProcessing.waiting_for_feedback, F.data.startswith("draft_edit_"))
async def process_draft_edit(callback: types.CallbackQuery, state: FSMContext):
    section_map = {
        "summary": "Про мене (Summary)",
        "experience": "Досвід роботи",
        "skills": "Навички",
        "projects": "Проєкти",
        "education": "Освіта",
        "languages": "Мови",
    }
    section_key = callback.data.replace("draft_edit_", "")
    section_name = section_map.get(section_key, section_key)

    await state.update_data(edit_section_key=section_key)
    await callback.message.edit_text(
        f"✏️ **Редагування розділу: {section_name}**\n\n"
        "Напиши, що саме ти хочеш змінити, додати або видалити. "
        "Можеш просто скинути свій готовий текст для цього розділу.",
        parse_mode="Markdown",
    )
    await state.set_state(VacancyProcessing.waiting_for_edit_prompt)


@router.message(VacancyProcessing.waiting_for_edit_prompt)
async def process_edit_prompt_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    wait_msg = await message.answer("⏳ ШІ вносить твої правки...")

    try:
        updated_json_str = await edit_cv_json(
            current_json=data['generated_cv_json'],
            section_to_edit=data['edit_section_key'],
            user_prompt=message.text,
            language=data['cv_language'],
        )

        await state.update_data(generated_cv_json=updated_json_str)
        await wait_msg.delete()
        await message.answer("✅ Правки успішно внесено!")
        await show_cv_draft(message, updated_json_str, state)

    except Exception as exc:  # noqa: BLE001 - boundary error is shown to the user
        await wait_msg.edit_text(f"❌ Помилка при редагуванні:\n{exc}")
        await show_cv_draft(message, data['generated_cv_json'], state)


@router.callback_query(VacancyProcessing.waiting_for_feedback, F.data == "draft_approve")
async def generate_final_pdf(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    profile_data = data['profile_data']
    user_id = callback.from_user.id

    await callback.message.edit_text("✅ Затверджено! Малюю PDF-документ... 🎨")

    photo_path = None
    if profile_data.get("photo_id"):
        try:
            bot = callback.bot
            photo_file = await bot.get_file(profile_data["photo_id"])
            photos_dir = os.path.join(os.getcwd(), "output", "photos")
            os.makedirs(photos_dir, exist_ok=True)
            photo_path = os.path.abspath(os.path.join(photos_dir, f"{user_id}.jpg"))
            if photo_file.file_path:
                await bot.download_file(photo_file.file_path, photo_path)
        except Exception as exc:  # noqa: BLE001 - photo failure is non-fatal
            print(f"Помилка завантаження фото: {exc}")

    profile_data["local_photo_path"] = photo_path
    file_name = f"CV_{profile_data['first_name']}_{profile_data['last_name']}.pdf"

    try:
        from bot.services.pdf_service import generate_pdf

        cv_data = json.loads(data['generated_cv_json'])
        cv_data = filter_driving_license(
            cv_data,
            data.get("vacancy_text", ""),
            data.get("additional_prompt", ""),
        )
        generated_cv_json = json.dumps(cv_data, ensure_ascii=False)

        pdf_path = generate_pdf(
            basic_info=profile_data,
            generated_cv_json=generated_cv_json,
            language=data['cv_language'],
            output_filename=file_name,
        )

        pdf_file = FSInputFile(pdf_path)
        await callback.message.answer_document(
            document=pdf_file,
            caption="🎉 Твоє ідеальне резюме готове! Успіхів на співбесіді!",
        )
        os.remove(pdf_path)
        await state.clear()
    except Exception as exc:  # noqa: BLE001 - boundary error is shown to the user
        await callback.message.answer(f"❌ Помилка рендерингу PDF:\n{exc}")
        await state.clear()