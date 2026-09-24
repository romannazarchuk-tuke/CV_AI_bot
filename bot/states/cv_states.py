from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    # Базові дані
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_email = State()
    waiting_for_phone = State()
    waiting_for_country = State()
    waiting_for_city = State()
    waiting_for_photo = State()

    # Досвід роботи
    waiting_for_experience = State()
    exp_initial_decision = State()
    exp_title = State()
    exp_company = State()
    exp_start = State()
    exp_end = State()
    exp_decision = State() 

    # Освіта 
    waiting_for_education = State()
    edu_initial_decision = State() # <--- Новий стан
    edu_inst = State()
    edu_degree = State()
    edu_field = State()
    edu_start = State()
    edu_is_studying = State() 
    edu_end_year = State()    
    edu_decision = State()

    # Мови
    lang_name = State()
    lang_level = State()
    lang_decision = State()
    
    # Навички, Права, Проєкти
    skills_input = State()
    waiting_for_driving_license = State()
    driving_license_category = State()
    waiting_for_linkedin = State()
    waiting_for_github = State()
    waiting_for_projects = State()

class VacancyProcessing(StatesGroup):
    waiting_for_vacancy_text = State()
    waiting_for_cv_language = State()
    waiting_for_additional_prompt = State()
    waiting_for_feedback = State() # Очікування натискання кнопки в меню чернетки
    waiting_for_edit_prompt = State() # Очікування тексту правки від користувача