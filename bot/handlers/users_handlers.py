import os
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from dotenv import load_dotenv
from bot.keyboards import get_task_type_ikb, task_type_cbd, duration_cbd, service_cbd, get_choose_student_ikb, \
    choose_student_cbd, get_help_kb, cancel_kb
from bot.states_groups import GetCertificateSG
from .user_utils import go_next_optional_field, registered, get_help_message, add_history, clear_history
from bot.models import session, User

s = session()

load_dotenv('.env')
tasks_limit = int(os.getenv('TASKS_LIMIT'))


# message handlers
async def cmd_help(msg: types.Message):
    await msg.delete()
    await msg.answer(get_help_message(msg.from_user), parse_mode='HTML', reply_markup=get_help_kb(msg.from_user))


async def cmd_cancel(msg: types.Message, state: FSMContext):
    await cmd_help(msg)
    await clear_history(state)
    await state.finish()


async def cmd_get(msg: types.Message):
    await msg.delete()
    if not registered(msg.from_user.id):
        await msg.answer('Для отправки запроса нужно войти в систему!')
        return

    user = s.query(User).where(User.id == msg.from_user.id).one()
    if user.active_requests >= tasks_limit:
        await msg.answer('Достигнуто максимальное количество активных заявок')
        return

    await msg.answer('Выберите тип заявки', reply_markup=get_task_type_ikb())


# callback query handlers
async def start_fill(cb: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await cb.message.delete()
    await GetCertificateSG.full_name.set()

    match callback_data['id']:
        case '1':
            async with state.proxy() as data:
                data['optional_fields'] = []
        case '2':
            async with state.proxy() as data:
                data['optional_fields'] = ['student_beneficiary', 'duration']
        case '3':
            async with state.proxy() as data:
                data['optional_fields'] = ['service']

    await add_history(await cb.message.answer('Пожалуйста, заполните данные для получения справки.\n'
                                              'Для отмены используйте /cancel.', reply_markup=cancel_kb), state)

    await GetCertificateSG.registered_data_get.set()

    async with state.proxy() as data:
        data['user'] = cb.from_user
        data['type_id'] = int(callback_data['id'])
        data['opt_fields_msgs'] = [GetCertificateSG.optional_fields_messages[f] for f in data['optional_fields']]

    user = s.query(User).where(User.id == cb.from_user.id).first()
    await cb.message.answer('Выберите ученика, для которого надо получить справку',
                            reply_markup=get_choose_student_ikb(user))


# message and callback handlers with states
async def choose_student(cb: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await cb.message.delete()
    async with state.proxy() as data:
        data['student_id'] = callback_data['id']

    await go_next_optional_field(cb.message, state)


async def get_beneficiary(cb: types.CallbackQuery, state: FSMContext):
    await add_history(cb.message, state)
    async with state.proxy() as data:
        if cb.data == 'is_beneficiary':
            data['student_beneficiary'] = True
        else:
            data['student_beneficiary'] = False

    await go_next_optional_field(cb.message, state)


async def get_duration(cb: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await cb.message.delete()
    async with state.proxy() as data:
        data['duration'] = int(callback_data['duration'])
    await go_next_optional_field(cb.message, state)


async def get_service(cb: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await cb.message.delete()
    async with state.proxy() as data:
        data['service_id'] = int(callback_data['id'])
    await go_next_optional_field(cb.message, state)


async def register_users_handlers(dp: Dispatcher):
    # message handlers
    dp.register_message_handler(cmd_help, commands=['start', 'help'])
    dp.register_message_handler(cmd_cancel, commands=['cancel'], state='*')
    dp.register_message_handler(cmd_get, commands=['get'])

    # callback query handlers
    dp.register_callback_query_handler(start_fill, task_type_cbd.filter())
    dp.register_callback_query_handler(choose_student, choose_student_cbd.filter(),
                                       state=GetCertificateSG.registered_data_get)
    dp.register_callback_query_handler(get_beneficiary, state=GetCertificateSG.student_beneficiary)
    dp.register_callback_query_handler(get_duration, duration_cbd.filter(), state=GetCertificateSG.duration)
    dp.register_callback_query_handler(get_service, service_cbd.filter(), state=GetCertificateSG.service)
