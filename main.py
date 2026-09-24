import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot.database.database import init_db
from bot.handlers import menu, registration, vacancy

# Загружаем переменные из .env
load_dotenv()

async def main():
    # Включаем логирование, чтобы видеть ошибки и статусы в консоли
    logging.basicConfig(level=logging.INFO)
    
    # Инициализируем базу данных (создаст файл cv_bot.db)
    await init_db()
    
    # Инициализируем бота и диспетчер
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    
    # Подключаем роутеры с хэндлерами
    dp.include_router(menu.router)
    dp.include_router(registration.router)
    dp.include_router(vacancy.router)
    
    print("🚀 Бот успешно запущен и готов к работе!")
    
    # Запускаем поллинг (ожидание обновлений от Telegram)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")