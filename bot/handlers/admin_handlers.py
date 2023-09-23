from dotenv import load_dotenv
from os import getenv
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from sqlalchemy.exc import NoResultFound
from bot.states_groups import FirstLoginSG, ViewTasksSG, BanSG, ViewBannedUsers
from bot.keyboards import get_close_task_ikb, close_task_cbd, get_help_kb, cancel_kb, get_unban_ikb, unban_cbd, \
    get_unban_confirm_ikb, unban_confirm_cbd
from .admin_utils import have_admin_rights, create_task_reply_message, ban_user, unban_user, create_banned_user_message
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


# ban system

# /ban command
async def cmd_ban(msg: types.Message, state: FSMContext):
    await msg.delete()
    if not have_admin_rights(msg.from_user):
        await msg.answer('Недостаточно прав для выполнения команды')
        return

    await BanSG.user_id.set()
    await add_history(await msg.answer('Введите ID пользователя для блокировки', reply_markup=cancel_kb), state)


async def get_ban_user_id(msg: types.Message, state: FSMContext):
    await add_history(msg, state)
    if msg.text == str(msg.from_user.id):
        await add_history(await msg.answer('Вы не можете заблокировать самого себя!'), state)
        return

    try:
        s.query(User).where(User.id == msg.text).one()
    except NoResultFound:
        await add_history(await msg.answer('Введёный ID некорректен, попробуйте ещё раз'), state)
        return

    async with state.proxy() as data:
        data['user_id'] = int(msg.text)
    await BanSG.next()
    await add_history(await msg.answer('Введите количество дней, на которые пользователь будет заблокировн'), state)


async def get_ban_duration(msg: types.Message, state: FSMContext):
    await add_history(msg, state)
    if not msg.text.isdigit():
        await msg.answer('Введённые данные некорректны, попробуйте ещё раз')
        return

    async with state.proxy() as data:
        ban_user(data['user_id'], int(msg.text))
        try:
            await msg.bot.send_message(data['user_id'], 'Ваш аккаунт был заблокирован')
        except:
            pass

    await clear_history(state)
    await msg.answer('Пользователь заблокирован', reply_markup=get_help_kb(msg.from_user))

    await state.finish()


# /banned_users command
async def cmd_banned_users(msg: types.Message, state: FSMContext):
    await msg.delete()
    if not have_admin_rights(msg.from_user):
        await msg.answer('Недостаточно прав для выполнения команды')
        return

    users = s.query(User).where(User.banned != 0).all()
    if not users:
        await msg.answer('Нет заблокированных пользователей')
        return

    await ViewBannedUsers.view.set()
    for user in users:
        await add_history(await msg.answer(create_banned_user_message(user),
                                           parse_mode='Markdown', reply_markup=get_unban_ikb(user)), state)
    await add_history(await msg.answer('Используйте /cancel для выхода из режима просмотра '
                                       'заблокированных пользователей', reply_markup=cancel_kb), state)


async def unban_button(cb: types.CallbackQuery, callback_data: dict,  state: FSMContext):
    await clear_history(state)

    index = callback_data['user'].find('_')
    user_id = callback_data['user'][:index]
    full_name = callback_data['user'][index + 1:]

    await cb.message.answer(f'Вы уверены, что хотите раблокировать пользователя {full_name}?',
                            reply_markup=get_unban_confirm_ikb(user_id))


async def unban_confirm_cancel(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await cb.message.answer('Закрыто', reply_markup=get_help_kb(cb.from_user))
    await state.finish()


async def unban_confirm(cb: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await cb.message.delete()
    unban_user(int(callback_data['id']))
    await cb.message.answer('Пользователь разблокирован', reply_markup=get_help_kb(cb.from_user))

    try:
        await cb.bot.send_message(int(callback_data['id']), 'Ваш аккаунт был разблокирован')
    except:
        pass

    await state.finish()


async def register_admin_handlers(dp: Dispatcher) -> None:
    # message handlers
    dp.register_message_handler(ask_first_time_password, commands=['admin_login'])
    dp.register_message_handler(login_first_admin, state=FirstLoginSG.password_input)
    dp.register_message_handler(add_admin, regexp='/add_admin @\w{4,32}')

    dp.register_message_handler(get_tasks, commands=['tasks'])

    # callback query handlers
    dp.register_callback_query_handler(close_task, close_task_cbd.filter(), state=ViewTasksSG.view)

    # ban system
    # /ban
    dp.register_message_handler(cmd_ban, commands=['ban'])
    dp.register_message_handler(get_ban_user_id, state=BanSG.user_id)
    dp.register_message_handler(get_ban_duration, state=BanSG.duration)
    # /banned_users
    dp.register_message_handler(cmd_banned_users, commands=['banned_users'])
    dp.register_callback_query_handler(unban_button, unban_cbd.filter(), state=ViewBannedUsers.view)
    dp.register_callback_query_handler(unban_confirm_cancel, text='unban_cancel', state=ViewBannedUsers.view)
    dp.register_callback_query_handler(unban_confirm, unban_confirm_cbd.filter(), state=ViewBannedUsers.view)
