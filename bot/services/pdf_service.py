import json
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import CSS, HTML

# Словник локалізації заголовків
TRANSLATIONS = {
    "English": {
        "summary": "Professional Summary",
        "experience": "Work Experience",
        "education": "Education",
        "skills": "Key Skills",
        "languages": "Languages",
        "projects": "Projects & Experience",
        "driving_license": "Driving License",
        "present": "Present"
    },
    "Slovak": {
        "summary": "Profesijné zhrnutie",
        "experience": "Pracovné skúsenosti",
        "education": "Vzdelanie",
        "skills": "Odborné zručності",
        "languages": "Jazykové znalosti",
        "projects": "Projekty a skúsenosti",
        "driving_license": "Vodičský preukaz",
        "present": "Súčasnosť"
    },
    "Ukrainian": {
        "summary": "Про мене",
        "experience": "Досвід роботи",
        "education": "Освіта",
        "skills": "Ключові навички",
        "languages": "Мовні навички",
        "projects": "Проєкти та досвід",
        "driving_license": "Водійське посвідчення",
        "present": "Дотепер"
    }
}


def _normalize_profile_url(value: object) -> str:
    """Додає HTTPS до URL профілю, якщо користувач не вказав схему."""
    url = str(value or "").strip()
    if not url or url == "Немає":
        return ""
    if url.startswith(("https://", "http://")):
        return url
    return f"https://{url}"


def generate_pdf(basic_info: dict, generated_cv_json: str, language: str, output_filename: str) -> str:
    """Генерує PDF-файл з HTML-шаблону та даних кандидата"""
    cv_data = json.loads(generated_cv_json)
    labels = TRANSLATIONS.get(language, TRANSLATIONS["English"])
    
    templates_dir = os.path.join(os.getcwd(), "bot", "templates")
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("cv_template.html")
    
    template_basic_info = dict(basic_info)
    template_basic_info["linkedin_url"] = _normalize_profile_url(basic_info.get("linkedin"))
    template_basic_info["github_url"] = _normalize_profile_url(basic_info.get("github"))

    html_content = template.render(
        basic=template_basic_info,
        cv=cv_data, 
        labels=labels
    )
    
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, output_filename)
    css_path = os.path.join(templates_dir, "style.css")
    
    HTML(string=html_content, base_url=templates_dir).write_pdf(
        output_path, 
        stylesheets=[CSS(filename=css_path, base_url=templates_dir)]
    )
    
    return output_path