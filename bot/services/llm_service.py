import asyncio
import os

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
ADDITIONAL_FALLBACK_MODELS = tuple(
    model.strip()
    for model in os.getenv(
        "GEMINI_ADDITIONAL_FALLBACK_MODELS",
        "gemini-3.6-flash-lite,gemini-3.7-flash,gemini-3.8-flash,"
        "gemini-flash-lite-latest,gemini-3-flash-preview",
    ).split(",")
    if model.strip()
)
MODEL_CANDIDATES = tuple(dict.fromkeys((PRIMARY_MODEL, FALLBACK_MODEL, *ADDITIONAL_FALLBACK_MODELS)))
TRANSIENT_ERROR_MARKERS = ("503", "UNAVAILABLE", "429", "500", "502", "504")


def _is_transient_provider_error(error: Exception) -> bool:
    message = str(error).upper()
    return any(marker in message for marker in TRANSIENT_ERROR_MARKERS)


def _is_unavailable_model_error(error: Exception) -> bool:
    message = str(error).upper()
    return "404" in message and "NOT_FOUND" in message


async def _generate_content_with_retries(client, contents: str, config):
    """Виконує обмежені повтори Gemini і переходить на резервну модель."""
    last_error = None
    for model_index, model in enumerate(MODEL_CANDIDATES):
        for attempt in range(2):
            try:
                return await client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
            except Exception as error:
                last_error = error
                is_last_attempt = model_index == len(MODEL_CANDIDATES) - 1 and attempt == 1
                if _is_unavailable_model_error(error):
                    break
                if not _is_transient_provider_error(error):
                    raise
                if is_last_attempt:
                    break
                await asyncio.sleep(2 ** attempt)

    if last_error is None:
        raise RuntimeError("Gemini generation failed: no model was configured")
    raise RuntimeError(
        f"Gemini generation failed after trying {', '.join(MODEL_CANDIDATES)}: "
        f"{last_error}"
    ) from last_error

# --- 1. Описуємо Pydantic-схеми для формату відповіді від Gemini ---

class Experience(BaseModel):
    title: str = Field(description="Посада")
    company: str = Field(description="Компанія")
    start_date: str = Field(description="Дата початку (напр., 09.2023)")
    end_date: str | None = Field(description="Дата закінчення або null, якщо працює зараз")
    is_current: bool = Field(description="Чи працює зараз")
    description: str = Field(description="Опис обов'язків та досягнень, адаптований під вакансію. Використовуй марковані списки.")

class Education(BaseModel):
    institution: str = Field(description="Навчальний заклад")
    degree: str = Field(description="Ступінь")
    field_of_study: str = Field(description="Спеціальність")
    start_year: str = Field(description="Рік початку")
    end_year: str = Field(description="Рік закінчення")

class Language(BaseModel):
    name: str = Field(description="Мова")
    level: str = Field(description="Рівень володіння")

class GeneratedCV(BaseModel):
    position_title: str = Field(
        description="Назва посади з вакансії, перекладена мовою резюме"
    )
    summary: str = Field(description="Коротке професійне summary (About me), ідеально адаптоване під вимоги вакансії.")
    skills: list[str] = Field(description="Список ключових навичок, відфільтрований та доповнений релевантними навичками з вакансії, якими володіє кандидат.")
    experience: list[Experience] = Field(description="Адаптований досвід роботи. Опис має підкреслювати релевантний для вакансії досвід.")
    education: list[Education] = Field(description="Освіта")
    languages: list[Language] = Field(description="Мови")
    driving_license: str = Field(description="Водійське посвідчення")
    projects: str = Field(description="Адаптований опис проєктів або загального досвіду.")


# --- 2. Функція виклику Gemini API ---

async def generate_cv_json(
    profile_data: dict, 
    vacancy_text: str, 
    language: str, 
    extra_prompt: str
) -> str:
    """Відправляє дані кандидата та вакансію до Gemini, повертає адаптований JSON."""
    
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    system_instruction = (
        f"Ти — професійний HR-експерт та резюме-райтер. Твоє завдання: адаптувати профіль кандидата "
        f"під вакансію і повернути конкретне, структуроване резюме у форматі JSON.\n"
        f"ОБОВ'ЯЗКОВА МОВА РЕЗЮМЕ ТА УСІХ ПОЛІВ: {language}. Переклади абсолютно всі текстові поля (summary, experience.description, projects тощо) цією мовою!\n\n"
        f"Правила:\n"
        f"1. 'position_title': точно визнач назву посади з вакансії та переклади її мовою резюме.\n"
        f"2. Пиши лаконічно, але не занадто коротко.\n"
        f"3. 'summary': не більше 2–3 містких речень.\n"
        f"4. В 'experience.description': використовуй 2–4 коротких маркованих пункти.\n"
        f"5. 'skills': тільки 8–12 найбільш релевантних навичок.\n"
        f"6. 'projects': виділи суть і технології.\n"
        f"7. Додаткові побажання користувача: {extra_prompt} — врахуй обов'язково.\n"
    )

    prompt = (
        f"--- ПРОФІЛЬ КАНДИДАТА ---\n{profile_data}\n\n"
        f"--- ВАКАНСІЯ ---\n{vacancy_text}"
    )

    response = await _generate_content_with_retries(
        client=client,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=GeneratedCV,
            temperature=0.7,
        ),
    )
    
    if not response.text:
        raise ValueError("Gemini returned an empty response")
    return response.text

async def edit_cv_json(
    current_json: str,
    section_to_edit: str,
    user_prompt: str,
    language: str,
) -> str:
    """Відправляє запит на точкове редагування конкретного розділу резюме."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    system_instruction = (
        "Ти — професійний HR-експерт. Користувач хоче внести правки у своє резюме.\n"
        f"ОБОВ'ЯЗКОВА МОВА: {language}.\n\n"
        f"Завдання: Зміни ТІЛЬКИ розділ '{section_to_edit}' у наданому JSON, "
        f"суворо дотримуючись вказівки користувача: '{user_prompt}'.\n"
        "Якщо користувач просить щось додати або видалити — зроби це акуратно, "
        "зберігаючи професійний тон.\n"
        f"ПОВЕРНИ ПОВНИЙ ОНОВЛЕНИЙ JSON. Усі інші розділи, крім '{section_to_edit}', "
        "залиш БЕЗ ЗМІН."
    )

    response = await _generate_content_with_retries(
        client=client,
        contents=current_json,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=GeneratedCV,
            temperature=0.7,
        ),
    )
    if not response.text:
        raise ValueError("Gemini returned an empty response")
    return response.text