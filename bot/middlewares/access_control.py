from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from typing import Callable, Dict, Any, Awaitable
from config.settings import settings


class AccessControlMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            user_id = str(event.from_user.id)
            chat_id = str(event.chat.id)

            allowed_users = settings.allowed_users.split(',')
            allowed_chats = settings.allowed_chats.split(',')

            # Check if the user is allowed
            # print(user_id)
            # print(allowed_users)
            # if user_id not in allowed_users:
            #     await event.reply("❌ You are not allowed to use this bot.")
            #     return  # Stop further processing
            
            # # Check if the chat is allowed
            # if chat_id not in allowed_chats:
            #     await event.reply("❌ This bot cannot be used in this chat.")
            #     return  # Stop further processing

        # Call the next handler
        return await handler(event, data)