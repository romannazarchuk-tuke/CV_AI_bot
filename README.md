# CV AI Bot

An intelligent Telegram Bot designed to help users generate professional, tailored Curriculum Vitaes (CVs) in PDF format using AI. The bot collects a user's profile information, takes a target job description (vacancy), and uses Google Gemini AI to adapt the resume specifically for that role.

## Features

- **Step-by-Step Profile Collection:** Gathers your basic info, work experience, education, skills, and languages right in Telegram.
- **AI-Powered Tailoring:** Uses Google Gemini API to analyze a job vacancy and adapt your summary, experience descriptions, and skills to highlight your most relevant qualifications.
- **High-Quality PDF Generation:** Automatically renders the AI-tailored resume into a sleek, professional PDF document using Jinja2 templates and WeasyPrint.
- **Multi-language Support:** Generates CVs in English, Slovak, and Ukrainian.
- **Interactive Editing:** Allows users to edit specific sections of their profile anytime.

## Tech Stack

- **Language:** Python 3.10+
- **Bot Framework:** [Aiogram 3](https://docs.aiogram.dev/en/latest/)
- **AI Integration:** Google GenAI (Gemini)
- **PDF Generation:** WeasyPrint + Jinja2 (HTML/CSS Templates)
- **Database:** SQLAlchemy + aiosqlite (Async SQLite)

## Installation and Setup

### 1. Prerequisites
- Python 3.10 or higher installed.
- A Telegram Bot Token (obtained from [@BotFather](https://t.me/botfather) in Telegram).
- A Google Gemini API Key (obtained from [Google AI Studio](https://aistudio.google.com/)).

### 2. Clone the repository
```bash
git clone https://github.com/romannazarchuk-tuke/CV_AI_bot.git
cd CV_AI_bot
```

### 3. Create a Virtual Environment and Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory (you can copy `.env.example` if it exists) and fill in your credentials:
```env
BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite+aiosqlite:///cv_bot.db
GEMINI_MODEL=gemini-3.5-flash-lite
```

### 5. Run the Bot
```bash
python main.py
```

## Project Structure

- `main.py` - Entry point for the application.
- `bot/handlers/` - Contains Telegram message handlers (registration, menu, etc.).
- `bot/database/` - SQLAlchemy models and database configuration.
- `bot/services/` - Core business logic, including `llm_service.py` (Gemini API calls) and `pdf_service.py` (PDF generation).
- `bot/templates/` - HTML, CSS, and assets (icons, fonts) used for styling the PDF.
- `bot/keyboards/` - Inline and reply keyboards for Telegram.
- `bot/states/` - FSM (Finite State Machine) definitions.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
