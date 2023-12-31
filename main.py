import asyncio
from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot.handlers.admin_handlers import register_admin_handlers
from bot.handlers.users_handlers import register_users_handlers
from bot.handlers.profile_handlers import register_profile_handlers
from bot.middleware import ThrottlingMiddleWare


async def register_handlers(dp: Dispatcher) -> None:
    await register_admin_handlers(dp)
    await register_users_handlers(dp)
    await register_profile_handlers(dp)

    dp.middleware.setup(ThrottlingMiddleWare(1))


async def main() -> None:
    load_dotenv('.env')
    token = os.getenv('TOKEN')

    bot = Bot(token)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    await register_handlers(dp)

    try:
        await dp.skip_updates()
        print('Бот запущен!')
        await dp.start_polling()
    except Exception as ex:
        print(f'[ERROR]: {ex}')


if __name__ == '__main__':
    asyncio.run(main())
