from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageToDeleteNotFound
from bot.handlers.admin_utils import have_admin_rights
from bot.states_groups import GetCertificateSG
from bot.keyboards import get_help_kb
from bot.models import session, Task, User


def registered(user_id: int) -> bool:
    s = session()
    res = bool(s.query(User).where(User.id == user_id).first())
    s.close()
    return res


def register_user(user_id, full_name, phone, url):
    s = session()
    if registered(user_id):
        user = s.query(User).where(User.id == user_id).first()
        user.full_name = full_name
        user.phone = phone
        s.add(user)
    else:
        s.add(User(id=user_id, full_name=full_name, phone=phone, url=url))

    s.commit()
    s.close()


def get_help_message(user):
    from .admin_handlers import login_first_admin
    reply_text = '<b><i>Список команд:</i></b>\n'\
                 '/cancel - принудительно завершить заполнение формы'

    if not login_first_admin.used:
        reply_text += '\n/admin_login - войти как администратор'

    if registered(user.id):
        reply_text += '\n/get - отправить заявку на справку'
        reply_text += '\n/profile - открыть профиль'
        reply_text += '\n/logout - выйти из системы <i>(аккаунт будет автоматически удалён)</i>'

        if have_admin_rights(user):
            reply_text += '\n/tasks - посмотерть список активных заявок' \
                          '\n/add_admin <b>@&lt;username пользователя&gt;</b> - ' \
                          'дать пользователю права администратора' \
                          '\n/ban - <b>заблокировать пользователя</b>' \
                          '\n/banned_users - <b>открыть список заблокированных польхователей для ' \
                          'просмотра и разблокировки</b>'

    else:
        reply_text += '\n/register - зарегистрироваться в системе'

    return reply_text


def convert_phone(phone: str) -> int | None:
    # clear phone
    phone = phone.replace('+7', '8')
    phone = phone.replace('-', '')
    phone = phone.replace('(', '')
    phone = phone.replace(')', '')
    phone = phone.replace(' ', '')

    if phone.isdigit() and len(phone) == 11:
        return int(phone)

    return None


def create_profile_message(user_id):
    s = session()
    user = s.query(User).where(User.id == user_id).first()

    res = ''
    if user.is_admin:
        res += '***admin***\n'

    res += f'***{user.full_name}***'

    if user.phone:
        res += f'\n_Телефон_: `{user.phone}`'
    if user.children:
        res += '\n_Дети_:'
    for c in user.children:
        res += f'\n{c.full_name} {c.clas}'
    return res


async def add_history(msg, state: FSMContext):
    async with state.proxy() as data:
        if data.get('history') is not None:
            data['history'].append(msg)
        else:
            data['history'] = [msg]


async def clear_history(state: FSMContext):
    async with state.proxy() as data:
        history = data.get('history')
        if history is None:
            return

        for m in history:
            try:
                await m.delete()
            except MessageToDeleteNotFound:
                pass


def save_task(data: dict) -> dict:
    s = session()

    user = s.query(User).where(User.id == data['user'].id).one()
    task = Task(
        type_id=data['type_id'],
        user_id=user.id,
        student_id=data['student_id'],

        student_beneficiary=data.get('student_beneficiary'),
        duration_in_month=data.get('duration'),
        service_id=data.get('service_id')
    )

    same_task = s.query(Task).where(
        Task.type_id == task.type_id
    ).where(
        Task.user_id == task.user_id
    ).where(
        Task.student_id == task.student_id
    ).where(
        Task.student_beneficiary == task.student_beneficiary
    ).where(
        Task.duration_in_month == task.duration_in_month
    ).where(Task.service_id == task.service_id).first()

    # if not same task in database
    if not same_task:

        s.add(task)
        s.commit()
        s.refresh(task)
        task.user.active_requests += 1
        res = {'full_name': task.user.full_name, 'type': task.type.name}
        s.add(task)
        s.commit()
    else:
        res = {}

    s.close()
    return res


async def go_next_optional_field(msg: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        if not data['optional_fields']:
            notification_data = save_task(data)

            await clear_history(state)
            await msg.answer('Ваша заявка принята на рассмотрение!', reply_markup=get_help_kb(data['user']))

            if notification_data:
                s = session()
                for admin in s.query(User).where(User.is_admin == 1).all():
                    await msg.bot.send_message(admin.id, f'{notification_data["full_name"]} оставил(а) '
                                                         f'запрос на "{notification_data["type"]}"')
                s.close()

            await state.finish()
            return

        next_state = getattr(GetCertificateSG, data["optional_fields"][0])
        await next_state.set()

        data['optional_fields'].pop(0)
        reply_msg = data['opt_fields_msgs'].pop(0)

    await add_history(await msg.answer(reply_msg['text'],
                                       reply_markup=reply_msg.get('reply_markup')), state)
