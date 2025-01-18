import asyncio
import logging
from bot.handlers.gmeet_handlers import router as gm_router
from bot.handlers.jira_handlers import router as jira_router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from bot.config.settings import settings
from aiogram import Bot, Dispatcher, F
from bot.middlewares.access_control import AccessControlMiddleware
from bot.database.models import async_main
# Initialize the bot

bot = Bot(token = settings.tg_bot_api_key )
dp = Dispatcher()
dp.message.middleware(AccessControlMiddleware())


@dp.message(CommandStart())
async def cmd_start(message: Message):    
    await message.reply(f"Welcome to the TG bot for Google Analytics ")



async def main():
    dp.include_router(gm_router)
    dp.include_router(jira_router)
    #await async_main()
    #await populate_users()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        print("Bot is running... Press Ctrl+C to stop.")
    except Exception as e:
        logging.error(f"Bot encountered an error: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
