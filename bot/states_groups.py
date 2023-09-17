from aiogram.dispatcher.filters.state import StatesGroup, State
from bot.keyboards import duration_ikb, get_service_ikb, beneficiary_ikb


class FirstLoginSG(StatesGroup):
    password_input = State()


class GetCertificateSG(StatesGroup):
    registered_data_get = State()
    full_name = State()
    student_fullname = State()
    student_class = State()
    student_beneficiary = State()
    duration = State()
    service = State()

    optional_fields_messages = {
        'duration': {'text': 'Выберите длительность питания в месяцах', 'reply_markup': duration_ikb},
        'service': {'text': 'Выберите дополнительную услугу', 'reply_markup': get_service_ikb()},
        'student_class': {'text': 'Введите класс ученика'},
        'student_beneficiary': {'text': 'Является ли ученик льготником?', 'reply_markup': beneficiary_ikb}
    }


class ViewTasksSG(StatesGroup):
    view = State()


class RegisterSG(StatesGroup):
    full_name = State()
    phone = State()
    student_full_name = State()
    student_class = State()


class ChangeFullName(StatesGroup):
    full_name = State()


class ChangePhoneSG(StatesGroup):
    phone = State()


class AddStudent(StatesGroup):
    student_full_name = State()
    student_class = State()
