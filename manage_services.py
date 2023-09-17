from bot.models import session, Service, Task

s = session()

service_names = [t[0] for t in s.query(Service.name).all()]

while True:
    print('Существующие услуги:\n' + ', '.join(service_names) + '\n')
    q = input('Введите название дополнительной услуги для добавления/удаления или нажмите [Enter] для выхода: ')
    if q == '':
        break

    if q in service_names:
        if input('Услуга уже существует. Удалить?(д/н) ').lower() in ('д', 'да'):
            service = s.query(Service).where(Service.name == q).one()
            tasks = s.query(Task).where(Task.service_id == service.id).all()

            s.delete(service)
            for t in tasks:
                s.delete(t)

            service_names.pop(service_names.index(q))

    else:
        if input(f'Добавить услугу {q}?(д/н) ').lower() in ('д', 'да'):
            service = Service(name=q)
            s.add(service)

            service_names.append(q)

s.commit()
input('Для того, чтобы изменеия вступили в силу, перезапустите бота\n ')
