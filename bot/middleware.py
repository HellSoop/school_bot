import datetime
from aiogram import Dispatcher, types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled
from aiogram.dispatcher.handler import CancelHandler
from bot.handlers.admin_utils import banned_users, unban_user


class ThrottlingMiddleWare(BaseMiddleware):
    def __init__(self, limit: int = 2):
        super().__init__()
        self.rate_limit = limit

    async def on_process_message(self, msg: types.Message, data: dict):
        dp = Dispatcher.get_current()

        try:
            await dp.throttle(key='antiflood_message', rate=self.rate_limit)
        except Throttled as _t:
            raise CancelHandler()


class BanMiddleWare(BaseMiddleware):
    async def on_process_message(self, msg: types.Message, data: dict):
        if msg.from_user.id in banned_users:
            if banned_users[msg.from_user.id] < datetime.date.today():
                unban_user(msg.from_user.id)
            else:
                raise CancelHandler()

    async def on_process_callback_query(self, cb: types.CallbackQuery, data: dict):
        if cb.from_user.id in banned_users:
            if banned_users[cb.from_user.id] < datetime.date.today():
                unban_user(cb.from_user.id)
            else:
                raise CancelHandler()
