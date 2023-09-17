from bot.models import session, User, Task


def have_admin_rights(user) -> bool:
    s = session()
    if user.username in have_admin_rights.unregistered_admins:

        user_obj = s.query(User).where(User.id == user.id).one()
        if user_obj is None:
            user_obj = User(id=user.id, is_admin=True)
        else:
            user_obj.is_admin = True

        s.add(user_obj)
        s.commit()
        s.close()

        have_admin_rights.unregistered_admins.pop(have_admin_rights.unregistered_admins.index(user.username))
        return True

    user_instance = s.query(User).where(User.id == user.id).where(User.is_admin == 1).first()
    s.close()
    return bool(user_instance)


have_admin_rights.unregistered_admins = []


def create_task_reply_message(task: Task) -> str:
    """
    Create message text to send to admin
    :param task: models.Task instance
    :return: str in Markdown format
    """
    reply_text = f'***{task.type.name}***\n' \
                 f'_ФИО родителя(законного представителя)_: {task.full_name}\n'

    if task.requesting_username is not None:
        reply_text += f'_Оставил пользователь_: @{task.requesting_username}\n'

    reply_text += f'_Телефон_: `{task.phone}`\n_ФИО ученика_: {task.student_full_name}'

    if task.student_class:
        reply_text += f'\n_Класс ученика_: {task.student_class}'
    if task.student_beneficiary:
        reply_text += f'\n_Льготник_'
    if task.duration_in_month is not None:
        reply_text += f'\n_Длительность(в месяцах)_: {task.duration_in_month}'
    if task.service_id is not None:
        reply_text += f'\n_Название услуги_: {task.service.name}'
    return reply_text
