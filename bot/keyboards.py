from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData
from bot.models import session, TaskType, Service, User

remove_student_cbd = CallbackData('remove_student', 'id')
logout_cbd = CallbackData('logout_confirm', 'confirm')
task_type_cbd = CallbackData('task_type_choose', 'id')
unban_cbd = CallbackData('unban_user', 'user')
unban_confirm_cbd = CallbackData('unban_confirm', 'id')
choose_student_cbd = CallbackData('student_choose', 'id')
duration_cbd = CallbackData('duration_choose', 'duration')
service_cbd = CallbackData('service_choose', 'id')
close_task_cbd = CallbackData('close_task', 'id')


# simple keyboards
def get_help_kb(user):
    from bot.handlers.admin_utils import have_admin_rights
    from bot.handlers.user_utils import registered

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if have_admin_rights(user):
        kb.add(KeyboardButton('/tasks'), KeyboardButton('/add_admin'))
    if registered(user.id):
        kb.add(KeyboardButton('/get'), KeyboardButton('/profile'), KeyboardButton('/logout'))
    else:
        kb.add(KeyboardButton('/get'), KeyboardButton('/register'))
    kb.add(InlineKeyboardButton('/help'))
    return kb


cancel_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton('/cancel')]], resize_keyboard=True)


# functions to get ikb
def get_remove_student_ikb(parent_id: int):
    s = session()
    parent = s.query(User).where(User.id == parent_id).first()

    ikb = InlineKeyboardMarkup()
    for c in parent.children:
        ikb.add(InlineKeyboardButton(c.full_name, callback_data=remove_student_cbd.new(c.id)))
    ikb.add(InlineKeyboardButton('Назад', callback_data='back_to_profile'))

    s.close()
    return ikb


def get_task_type_ikb():
    s = session()
    ikb = InlineKeyboardMarkup()

    tasks_types = s.query(TaskType).all()
    for t in tasks_types:
        ikb.add(InlineKeyboardButton(t.name, callback_data=task_type_cbd.new(t.id)))

    s.close()
    return ikb


def get_unban_ikb(user: User):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Разблокировать', callback_data=unban_cbd.new(f'{user.id}_{user.full_name}'))
         ]])


def get_unban_confirm_ikb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Да', callback_data=unban_confirm_cbd.new(user_id)),
         InlineKeyboardButton('Нет', callback_data='unban_cancel')]
    ])


def get_choose_student_ikb(user: User):
    ikb = InlineKeyboardMarkup()
    for c in user.children:
        ikb.add(InlineKeyboardButton(c.full_name, callback_data=choose_student_cbd.new(c.id)))
    return ikb


def get_service_ikb():
    s = session()
    ikb = InlineKeyboardMarkup()

    for service in s.query(Service).all():
        ikb.add(InlineKeyboardButton(service.name, callback_data=service_cbd.new(service.id)))
    s.close()
    return ikb


def get_close_task_ikb(task_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton('Закрыть', callback_data=close_task_cbd.new(task_id))
    ]])


# simple ikb
register_continue_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton('Завершить', callback_data='register_continue')]
])

profile_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton('Активные заявки', callback_data='requests')],
    [InlineKeyboardButton('Изменить ФИО', callback_data='change_full_name')],
    [InlineKeyboardButton('Изменить телефон', callback_data='change_phone')],
    [InlineKeyboardButton('Добавть ребёнка', callback_data='add_student')],
    [InlineKeyboardButton('Удалить ребёнка', callback_data='remove_student')],
])


back_to_profile_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton('Назад', callback_data='back_to_profile')]
])


beneficiary_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton('Да', callback_data='is_beneficiary'),
     InlineKeyboardButton('Нет', callback_data='not_beneficiary')]
])


logout_confirm_ikb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton('Да', callback_data=logout_cbd.new(True)),
        InlineKeyboardButton('Нет', callback_data=logout_cbd.new(False))
    ]])

duration_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton('3 месяца', callback_data=duration_cbd.new(3))],
    [InlineKeyboardButton('6 месяцев', callback_data=duration_cbd.new(6))],
    [InlineKeyboardButton('9 месяцев', callback_data=duration_cbd.new(9))]
])
