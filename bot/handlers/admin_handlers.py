from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from bot.states_groups import FirstLoginSG, ViewTasksSG
from dotenv import load_dotenv
from os import getenv
from bot.keyboards import get_close_task_ikb, close_task_cbd, get_help_kb, cancel_kb
from .admin_utils import have_admin_rights, create_task_reply_message
from .user_utils import registered, add_history, clear_history
from bot.models import session, User, Task

s = session()

load_dotenv('././.env')
first_time_password = getenv('FIRST_TIME_PASSWORD')


# message handlers
async def ask_first_time_password(msg: types.Message, state: FSMContext):
    await msg.delete()

    if not login_first_admin.used:
        await FirstLoginSG.password_input.set()
        await add_history(await msg.answer('Введите пароль для первого входа:'), state)
    else:
        await msg.answer('Первый вход уже был совершён')


async def login_first_admin(msg: types.Message, state: FSMContext):
    await msg.delete()
    await clear_history(state)

    if msg.text == first_time_password:
        if registered(msg.from_user.id):
            user = s.query(User).where(User.id == msg.from_user.id).first()
            user.is_admin = True
            s.add(user)
        else:
            s.add(User(id=msg.from_user.id, is_admin=True, url=msg.from_user.url))
        s.commit()
        login_first_admin.used = True

        await msg.answer('Вы вошли в систему!', reply_markup=get_help_kb(msg.from_user))
    else:
        await msg.answer('Неверный пароль')

    await state.finish()


login_first_admin.used = bool(s.query(User.id).where(User.is_admin == 1).first())


async def add_admin(msg: types.Message):
    if not have_admin_rights(msg.from_user):
        await msg.answer('Недостаточно прав для выполнения этой команды')
        return

    await msg.delete()
    username = msg.text[msg.text.find('@') + 1:]
    have_admin_rights.unregistered_admins.append(username)
    await msg.answer(f'Пользователь @{username} добавлен к администраторам. '
                     f'Изменеия будут сохранены после первой выпоненой им команды.')


async def get_tasks(msg: types.Message, state: FSMContext):
    await msg.delete()
    if not have_admin_rights(msg.from_user):
        await msg.answer('Недостаточно прав для выполнения этой команды')
        return

    tasks: list[Task] = s.query(Task).all()
    if not tasks:
        await msg.answer('На данный момент заявлений нет')
        return

    await ViewTasksSG.view.set()
    for t in tasks:
        await add_history(await msg.answer(create_task_reply_message(t),
                                           parse_mode='Markdown', reply_markup=get_close_task_ikb(t.id)), state)

    await add_history(await msg.answer('/cancel, чтобы выйти из режима просмтотра заявлнений',
                                       reply_markup=cancel_kb), state)


# callback query handlers
async def close_task(cb: types.CallbackQuery, callback_data: dict):
    task = s.query(Task).where(Task.id == int(callback_data['id'])).first()
    await cb.answer('Заявление закрыто', show_alert=True)
    await cb.message.delete()

    if task is not None:
        task.user.active_requests -= 1
        s.add(task)
        s.delete(task)
        s.commit()


async def register_admin_handlers(dp: Dispatcher) -> None:
    # message handlers
    dp.register_message_handler(ask_first_time_password, commands=['admin_login'])
    dp.register_message_handler(login_first_admin, state=FirstLoginSG.password_input)
    dp.register_message_handler(add_admin, regexp='/add_admin @\w{4,32}')

    dp.register_message_handler(get_tasks, commands=['tasks'])

    # callback query handlers
    dp.register_callback_query_handler(close_task, close_task_cbd.filter(), state=ViewTasksSG.view)
