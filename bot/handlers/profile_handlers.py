from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageToDeleteNotFound

import bot.models
from bot.handlers.admin_handlers import login_first_admin
from bot.handlers.user_utils import create_profile_message, register_user, registered, add_history, clear_history, \
    convert_phone
from bot.keyboards import profile_ikb, logout_confirm_ikb, register_continue_ikb, logout_cbd, get_remove_student_ikb, \
    remove_student_cbd, back_to_profile_ikb, get_help_kb, cancel_kb
from bot.states_groups import RegisterSG, ChangeFullName, AddStudent, ChangePhoneSG
from bot.models import session, User, Student

s = session()


# commands handlers
async def cmd_register(msg: types.Message, state: FSMContext):
    await msg.delete()
    if registered(msg.from_user.id):
        # check for case, when user is admin, but not registered
        user = s.query(User).where(User.id == msg.from_user.id).one()
        if user.full_name:
            await msg.answer('Вы уже вошли в систему!')
            return

    await RegisterSG.full_name.set()
    await add_history(await msg.answer('Введите свои ФИО', reply_markup=cancel_kb), state)


async def cmd_profile(msg: types.Message):
    try:
        await msg.delete()
    except MessageToDeleteNotFound:
        pass

    if not registered(msg.from_user.id):
        await msg.answer('Вы не вошли в систему')
        return
    await msg.answer(create_profile_message(msg.from_user.id), parse_mode='Markdown', reply_markup=profile_ikb)


async def logout(msg: types.Message):
    await msg.delete()
    if not registered(msg.from_user.id):
        await msg.answer('Вы не вошли в систему')
        return
    await msg.answer('Вы уверены, что хотите выйти из аккаунта?', reply_markup=logout_confirm_ikb)


# callback query handlers
async def finish_registration(cb: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        register_user(user_id=cb.from_user.id, full_name=data['full_name'], phone=data['phone'], url=data['url'])
        try:
            s.add_all([Student(full_name=c['full_name'], parent_id=cb.from_user.id,
                               clas=c['class']) for c in data['children']])
        except KeyError:
            pass
        s.commit()

    await clear_history(state)
    await state.finish()
    await cb.message.answer('Вы зарегистрировались в системе!', reply_markup=get_help_kb(cb.from_user))
    await return_to_profile(cb)


# profile buttons
async def active_requests_button(cb: types.CallbackQuery):
    await cb.message.delete()

    user = s.query(User).where(User.id == cb.from_user.id).one()

    reply_text = ''
    if user.active_requests:
        reply_text += '***Активные заявки***'
        for task in user.requests:
            reply_text += f'\n\n"{task.type.name}" для {task.student.full_name}'
    else:
        reply_text += 'Нет активных заявок'

    await cb.message.answer(reply_text, reply_markup=back_to_profile_ikb, parse_mode='Markdown')


async def change_full_name_button(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.delete()
    if not registered(cb.from_user.id):
        await cb.answer('Вы не вошли в систему')
        return

    await ChangeFullName.full_name.set()
    await add_history(await cb.message.answer('Введите изменённые ФИО'), state)


async def change_phone_button(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.delete()

    if not registered(cb.from_user.id):
        await cb.answer('Вы не вошли в систему')
        return

    await ChangePhoneSG.phone.set()
    await add_history(await cb.message.answer('Введите новый номер телефона'), state)


async def add_student_button(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.delete()
    if not registered(cb.from_user.id):
        await cb.answer('Вы не вошли в систему')
        return

    await AddStudent.student_full_name.set()

    request_msg = await cb.message.answer('Введите ФИО ученика', reply_markup=back_to_profile_ikb)
    await add_history(request_msg, state)


async def remove_student_button(cb: types.CallbackQuery):
    await cb.message.delete()
    if not registered(cb.from_user.id):
        await cb.answer('Вы не вошли в систему')
        return

    await cb.message.answer('Выберите ученика для удаления', reply_markup=get_remove_student_ikb(cb.from_user.id))


async def remove_student(cb: types.CallbackQuery, callback_data: dict):
    student = s.query(Student).where(Student.id == callback_data['id']).first()
    s.delete(student)
    s.commit()
    await return_to_profile(cb)


async def return_to_profile(cb: types.CallbackQuery, state: FSMContext | None = None):
    if state is not None:
        await state.finish()
    try:
        await cb.message.delete()
    except MessageToDeleteNotFound:
        pass
    await cb.message.answer(create_profile_message(cb.from_user.id), parse_mode='Markdown', reply_markup=profile_ikb)


async def handle_logout_confirm(cb: types.CallbackQuery, callback_data: dict):
    if callback_data['confirm'] == 'True':
        user = s.query(User).where(User.id == cb.from_user.id).first()
        s.delete(user)
        s.commit()

        if user.is_admin:
            login_first_admin.used = bool(s.query(User.id).where(User.is_admin == 1).first())
        await cb.answer('Вы вышли из системы', show_alert=True)

    await cb.message.delete()


# message handlers with states
async def get_register_fullname(msg: types.Message, state: FSMContext):
    await add_history(msg, state)
    async with state.proxy() as data:
        data['full_name'] = msg.text
        data['url'] = msg.from_user.url
        data['children'] = []

    await add_history(await msg.answer('Введите ваш мобильный телефон'), state)
    await RegisterSG.next()


async def get_register_phone(msg: types.Message, state: FSMContext):
    await add_history(msg, state)
    phone = convert_phone(msg.text)

    if phone is None:
        await add_history(await msg.answer('Введённый телефон не корректен, попробуйте ещё раз'), state)
        return

    async with state.proxy() as data:
        data['phone'] = phone

    await add_history(await msg.answer('Введите ФИО ученика'), state)
    await RegisterSG.next()


async def get_register_student_name(msg: types.Message, state: FSMContext):
    await add_history(msg, state)
    async with state.proxy() as data:
        data['children'].append({'full_name': msg.text})

    await add_history(await msg.answer('Введите класс учениека'), state)
    await RegisterSG.next()


async def get_register_student_class(msg: types.Message, state: FSMContext):
    await add_history(msg, state)
    async with state.proxy() as data:
        data['children'][-1]['class'] = msg.text
    await add_history(await msg.answer('Ученик сохранён. Нажмите на кнопку, чтобы продолжить или'
                                       ' введите имя следующего', reply_markup=register_continue_ikb), state)

    await RegisterSG.student_full_name.set()


async def change_full_name(msg: types.Message, state: FSMContext):
    await clear_history(state)
    user = s.query(User).where(User.id == msg.from_user.id).first()
    user.full_name = msg.text
    s.add(user)
    s.commit()
    await state.finish()
    await cmd_profile(msg)


async def change_phone(msg: types.Message, state: FSMContext):
    await add_history(msg, state)
    phone = convert_phone(msg.text)

    if phone is None:
        await add_history(await msg.answer('Введённый телефон не корректен, попробуйте ещё раз'), state)
        return

    user = s.query(User).where(User.id == msg.from_user.id).one()
    user.phone = phone
    s.add(user)
    s.commit()

    await clear_history(state)
    await state.finish()
    await cmd_profile(msg)


async def get_add_student_full_name(msg: types.Message, state: FSMContext):
    await add_history(msg, state)
    async with state.proxy() as data:
        data['full_name'] = msg.text
    await AddStudent.next()
    await add_history(await msg.answer('Введите класс ученика'), state)


async def add_student(msg: types.Message, state: FSMContext):
    await clear_history(state)

    async with state.proxy() as data:
        s.add(Student(full_name=data['full_name'],  clas=msg.text, parent_id=msg.from_user.id))
        s.commit()

    await state.finish()
    await cmd_profile(msg)  # also delete message with class


async def register_profile_handlers(dp: Dispatcher):
    # command handlers
    dp.register_message_handler(cmd_register, commands=['register'])
    dp.register_message_handler(cmd_profile, commands=['profile'])
    dp.register_message_handler(logout, commands=['logout'])

    # callback query handlers
    dp.register_callback_query_handler(finish_registration, text='register_continue',
                                       state=RegisterSG.student_full_name)
    # profile buttons
    dp.register_callback_query_handler(active_requests_button, text='requests')
    dp.register_callback_query_handler(change_full_name_button, text='change_full_name')
    dp.register_callback_query_handler(change_phone_button, text='change_phone')
    dp.register_callback_query_handler(remove_student_button, text='remove_student')
    dp.register_callback_query_handler(remove_student, remove_student_cbd.filter())
    dp.register_callback_query_handler(return_to_profile, text='back_to_profile', state='*')
    dp.register_callback_query_handler(add_student_button, text='add_student')

    dp.register_callback_query_handler(handle_logout_confirm, logout_cbd.filter())

    # message handlers with states
    dp.register_message_handler(get_register_fullname, state=RegisterSG.full_name)
    dp.register_message_handler(get_register_student_name, state=RegisterSG.student_full_name)
    dp.register_message_handler(get_register_phone, state=RegisterSG.phone)
    dp.register_message_handler(get_register_student_class, state=RegisterSG.student_class)
    dp.register_message_handler(change_full_name, state=ChangeFullName.full_name)
    dp.register_message_handler(change_phone, state=ChangePhoneSG.phone)
    dp.register_message_handler(get_add_student_full_name, state=AddStudent.student_full_name)
    dp.register_message_handler(add_student, state=AddStudent.student_class)
