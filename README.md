# 🤖 AI-Powered CV & Resume Builder Telegram Bot

A sophisticated Telegram bot built with **Python (aiogram)** and the **Google Gemini API** that helps users generate tailored, localized (Ukrainian/Slovak/English) PDF resumes adapted specifically to target job descriptions.

---

## ✨ Key Features

- **🎯 Smart Vacancy Adaptation:** Analyzes job descriptions via Gemini and aligns the user's professional profile, summary, and experience to match key requirements.
- **🌐 Multi-Language Support:** Generates resumes in Ukrainian, Slovak, or English with localized labels and correct formatting.
- **✏️ Interactive "Draft-Edit-Approve" Workflow:** 
  - Generates a text draft of the CV first.
  - Provides a structured Ukrainian inline keyboard to review and edit specific sections (Summary, Experience, Skills, Projects, Education, Languages).
  - Uses targeted LLM prompts to update only the selected section based on user feedback.
- **🎨 Professional PDF Generation:** Renders clean, modern, print-ready PDF resumes using **WeasyPrint** and **Jinja2** HTML templates, complete with custom styled photos and optional GitHub/LinkedIn links.
- **🧠 Smart Control Logic:** Automatically handles conditional sections (e.g., automatically omitting driving licenses if the vacancy doesn't require them, unless requested via custom prompts).
- **🗄️ Robust State Management:** Powered by `aiogram` FSM and stored securely using SQLAlchemy (SQLite/PostgreSQL).

---

## 🛠️ Tech Stack

- **Core:** Python 3.10+, aiogram 3.x
- **AI / LLM:** Google Gemini API (`gemini-flash` models), Pydantic (for strict JSON schema validation)
- **Database:** SQLAlchemy, SQLite / PostgreSQL
- **PDF & Templating:** WeasyPrint, Jinja2, HTML/CSS
- **Environment Management:** python-dotenv
