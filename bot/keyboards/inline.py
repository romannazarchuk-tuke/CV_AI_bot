from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_current_job_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для вопроса 'Работаете ли вы здесь сейчас?'"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Так, працюю зараз", callback_data="job_current_yes"),
            InlineKeyboardButton(text="❌ Ні, вже не працюю", callback_data="job_current_no")
        ]
    ])

def get_add_more_keyboard(block_name: str) -> InlineKeyboardMarkup:
    """Клавиатура для добавления еще одной записи или перехода дальше"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати ще", callback_data=f"add_more_{block_name}")],
        [InlineKeyboardButton(text="➡️ Продовжити", callback_data=f"continue_{block_name}")]
    ])

def get_is_studying_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для статусу навчання"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Ще вчуся", callback_data="edu_studying_yes")],
        [InlineKeyboardButton(text="✅ Вже закінчив/ла", callback_data="edu_studying_no")]
    ])

def get_language_level_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору рівня мови"""
    levels = [
        "A1 - Beginner", "A2 - Elementary", 
        "B1 - Intermediate", "B2 - Upper Intermediate", 
        "C1 - Advanced", "C2 - Proficient"
    ]
    keyboard = [[InlineKeyboardButton(text=lvl, callback_data=f"lang_lvl_{lvl.split(' - ')[0]}")] for lvl in levels]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_start_experience_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для старту блоку досвіду"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Додати досвід", callback_data="exp_add_yes")],
        [InlineKeyboardButton(text="⏭ Немає досвіду", callback_data="exp_add_no")]
    ])

def get_has_license_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура: наявність прав"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Так, є", callback_data="has_license_yes")],
        [InlineKeyboardButton(text="❌ Немає", callback_data="has_license_no")]
    ])

def get_license_category_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура: вибір категорії"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A", callback_data="lic_cat_A"), InlineKeyboardButton(text="B", callback_data="lic_cat_B")],
        [InlineKeyboardButton(text="C", callback_data="lic_cat_C"), InlineKeyboardButton(text="D", callback_data="lic_cat_D")],
        [InlineKeyboardButton(text="B, C", callback_data="lic_cat_BC")],
        [InlineKeyboardButton(text="✍️ Написати власну", callback_data="lic_cat_other")]
    ])

def get_skip_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Універсальна кнопка пропуску"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустити", callback_data=callback_data)]
    ])

def get_cv_language_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору мови резюме"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_English")],
        [InlineKeyboardButton(text="🇸🇰 Словацька", callback_data="lang_Slovak")],
        [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_Ukrainian")]
    ])

def get_edit_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору розділу для зміни"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Базова інформація", callback_data="edit_basic")],
        [InlineKeyboardButton(text="💼 Досвід роботи", callback_data="edit_experience")],
        [InlineKeyboardButton(text="🎓 Освіта", callback_data="edit_education")],
        [InlineKeyboardButton(text="🗣 Мови", callback_data="edit_languages")],
        [InlineKeyboardButton(text="🛠 Навички та інше", callback_data="edit_skills")],
        [InlineKeyboardButton(text="🔗 LinkedIn", callback_data="edit_linkedin")],
        [InlineKeyboardButton(text="💻 GitHub", callback_data="edit_github")]
    ])

def get_edit_link_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для зміни або видалення посилання."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Видалити посилання", callback_data="delete_link")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_edit")]
    ])

def get_start_education_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для старту блоку освіти"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Додати освіту", callback_data="edu_add_yes")],
        [InlineKeyboardButton(text="⏭ Немає освіти", callback_data="edu_add_no")]
    ])

def get_degree_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору ступеня"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Bachelor's Degree", callback_data="deg_Bachelor")],
        [InlineKeyboardButton(text="Master's Degree", callback_data="deg_Master")],
        [InlineKeyboardButton(text="Assoc. Degree / Diploma", callback_data="deg_Assoc")],
        [InlineKeyboardButton(text="High School", callback_data="deg_High")],
        [InlineKeyboardButton(text="✍️ Написати інше", callback_data="deg_Other")]
    ])

def get_finish_vacancy_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для завершення введення довгої вакансії"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Завершити введення", callback_data="vacancy_finished")]
    ])

def get_cv_draft_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для редагування чернетки резюме"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Все супер, згенерувати PDF", callback_data="draft_approve")],
        [
            InlineKeyboardButton(text="✏️ Про мене (Summary)", callback_data="draft_edit_summary"),
            InlineKeyboardButton(text="✏️ Досвід роботи", callback_data="draft_edit_experience")
        ],
        [
            InlineKeyboardButton(text="✏️ Навички", callback_data="draft_edit_skills"),
            InlineKeyboardButton(text="✏️ Проєкти", callback_data="draft_edit_projects")
        ],
        [
            InlineKeyboardButton(text="✏️ Освіта", callback_data="draft_edit_education"),
            InlineKeyboardButton(text="✏️ Мови", callback_data="draft_edit_languages")
        ]
    ])