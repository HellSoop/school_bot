import datetime
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
                 f'_ФИО родителя(законного представителя)_: `{task.user.full_name}`\n' \
                 f'ID пользователя: `{task.user_id}`\n' \
                 f'[Аккаунт пользователя]({task.user.url})\n' \
                 f'_Телефон_: `{task.user.phone}`\n_ФИО ученика_: {task.student.full_name}'

    if task.type_id == 1:
        reply_text += f'\n_Класс ученика_: {task.student.clas}'
    if task.student_beneficiary:
        reply_text += f'\n_Льготник_'
    if task.duration_in_month is not None:
        reply_text += f'\n_Длительность(в месяцах)_: {task.duration_in_month}'
    if task.service_id is not None:
        reply_text += f'\n_Название услуги_: {task.service.name}'
    return reply_text


ses = session()
banned_users = {i: d for i, d in ses.query(User.id, User.banned).all() if d is not None}
ses.close()


def ban_user(user_id: int, duration: int) -> None:
    """
    Ban user by ID
    :param user_id: user ID
    :param duration: duration of ban by days
    :return: None
    """

    s = session()
    user = s.query(User).where(User.id == user_id).one()

    user.banned = datetime.date.today() + datetime.timedelta(days=duration)
    banned_users[user_id] = user.banned

    s.add(user)
    s.commit()
    s.close()


def unban_user(user_id: int):
    s = session()
    user = s.query(User).where(User.id == user_id).one()

    user.banned = None
    del banned_users[user_id]

    s.add(user)
    s.commit()
    s.close()
