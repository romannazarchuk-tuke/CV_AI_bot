import json

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.database.database import async_session
from bot.database.models import User
from bot.handlers.registration import start_education, start_experience
from bot.keyboards.inline import (
    get_edit_link_keyboard,
    get_edit_profile_keyboard,
    get_finish_vacancy_keyboard,
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.states.cv_states import Registration, VacancyProcessing

router = Router()

@router.message(F.text == "📝 Надіслати вакансію")
async def menu_send_vacancy(message: types.Message, state: FSMContext):
    await state.update_data(vacancy_text="") # Очищаємо попередню вакансію
    await message.answer(
        "Надішли мені текст вакансії (або вимоги до кандидата).\n\n"
        "⚠️ Якщо текст дуже довгий, Telegram розіб'є його на кілька повідомлень. "
        "Просто надішли їх усі, а коли закінчиш — натисни кнопку нижче.",
        reply_markup=get_finish_vacancy_keyboard()
    )
    await state.set_state(VacancyProcessing.waiting_for_vacancy_text)
@router.message(F.text == "👀 Переглянути профіль")
async def menu_view_profile(message: types.Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
    if not user or not user.profile_data:
        await message.answer("Твій профіль ще порожній. Натисни /start, щоб заповнити.")
        return
        
    data = json.loads(user.profile_data)
    
    # Форматування списків для красивого виводу
    def format_exp(exp_list):
        if not exp_list: return "Немає"
        return "\n".join([f"• {e['title']} в {e['company']} ({e.get('start_date', '')} - {e.get('end_date') or 'дотепер'})" for e in exp_list])

    def format_edu(edu_list):
        if not edu_list: return "Немає"
        return "\n".join([f"• {e.get('degree', '')}, {e.get('institution', '')} ({e.get('start_year', '')} - {e.get('end_year', '')})" for e in edu_list])

    def format_lang(lang_list):
        if not lang_list: return "Немає"
        return "\n".join([f"• {l['name']} ({l['level']})" for l in lang_list])
    
    text = f"👤 **Ім'я:** {data.get('first_name', '')} {data.get('last_name', '')}\n"
    text += f"📧 **Email:** {data.get('email', '')}\n"
    text += f"📞 **Телефон:** {data.get('phone', '')}\n"
    text += f"📍 **Локація:** {data.get('city', '')}, {data.get('country', '')}\n\n"
    
    text += f"💼 **Досвід роботи:**\n{format_exp(data.get('experience', []))}\n\n"
    text += f"🎓 **Освіта:**\n{format_edu(data.get('education', []))}\n\n"
    text += f"🗣 **Мови:**\n{format_lang(data.get('languages', []))}\n\n"
    if data.get("linkedin") and data.get("linkedin") != "Немає":
        text += f"🔗 **LinkedIn:** {data['linkedin']}\n"
    if data.get("github") and data.get("github") != "Немає":
        text += f"💻 **GitHub:** {data['github']}\n"
    text += f"🛠 **Навички:** {', '.join(data.get('skills', []))}\n"
    text += f"🚗 **Права:** {data.get('driving_license', 'Немає')}\n"
    text += f"🚀 **Проєкти/Інше:** {data.get('projects', 'Не вказано')}"
    
    photo_id = data.get("photo_id")
    
    # Перевіряємо довжину тексту (ліміт Telegram для підпису фото — 1024 символи)
    if photo_id:
        if len(text) <= 1000:
            await message.answer_photo(photo=photo_id, caption=text, parse_mode="Markdown")
        else:
            # Якщо текст задовгий, відправляємо фото окремо, а текст звичайним повідомленням
            await message.answer_photo(photo=photo_id)
            
            # Якщо текст раптом перевищує навіть ліміт текстового повідомлення (4096), б'ємо його на частини
            for i in range(0, len(text), 4000):
                await message.answer(text[i:i+4000], parse_mode="Markdown")
    else:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i+4000], parse_mode="Markdown")
            
@router.message(F.text == "✏️ Змінити інформацію")
async def menu_edit_info(message: types.Message):
    await message.answer("Який розділ ти хочеш змінити?", reply_markup=get_edit_profile_keyboard())

# --- Обробка кнопок редагування ---
@router.callback_query(F.data.startswith("edit_"))
async def process_edit_profile(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Встановлюємо прапорець редагування
    await state.update_data(is_editing=True)
    
    if action == "edit_basic":
        await callback.message.answer("Починаємо зміну базової інформації.\nНапиши своє ім'я:")
        await state.set_state(Registration.waiting_for_first_name)
    
    elif action == "edit_experience":
        await state.set_state(Registration.waiting_for_experience)
        await start_experience(callback.message, state) 
        
    elif action == "edit_education":
        await state.set_state(Registration.waiting_for_education)
        await start_education(callback.message, state)
        
    elif action == "edit_languages":
        await state.update_data(languages_list=[]) # Очищаємо старі мови
        await callback.message.answer("Окей, додаємо мови наново. Напиши мову (наприклад, English):")
        await state.set_state(Registration.lang_name)
        
    elif action == "edit_skills":
        await callback.message.answer("Напиши свої ключові навички через кому (це замінить старі):")
        await state.set_state(Registration.skills_input)

    elif action in {"edit_linkedin", "edit_github"}:
        link_name = "LinkedIn" if action == "edit_linkedin" else "GitHub"
        link_key = action.replace("edit_", "")
        await state.update_data(editing_link=link_key)
        await callback.message.answer(
            f"Надішли нове посилання на {link_name} або видали його:",
            reply_markup=get_edit_link_keyboard(),
        )
        await state.set_state(
            Registration.waiting_for_linkedin
            if link_key == "linkedin"
            else Registration.waiting_for_github
        )


@router.callback_query(F.data == "delete_link")
async def delete_link(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    link_key = data.get("editing_link")
    if link_key not in {"linkedin", "github"}:
        await callback.answer("Спочатку обери LinkedIn або GitHub.", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar_one()
        profile = json.loads(user.profile_data)
        profile[link_key] = "Немає"
        user.profile_data = json.dumps(profile, ensure_ascii=False)
        await session.commit()

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✅ Посилання видалено.", reply_markup=get_main_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == "cancel_edit")
async def cancel_link_edit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Редагування скасовано.", reply_markup=get_main_menu_keyboard())
    await state.clear()