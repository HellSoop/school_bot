from aiogram import Dispatcher, types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled
from aiogram.dispatcher.handler import CancelHandler


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
