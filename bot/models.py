from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base

engine = create_engine('sqlite:///bot.db')
session = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    full_name = Column(String(256), nullable=True, default=None)
    url = Column(String(64), nullable=False)
    phone = Column(Integer, nullable=True, default=None)
    active_requests = Column(Integer, default=0)
    banned = Column(Date, nullable=True)

    children = relationship('Student', back_populates='parent', cascade='save-update, merge, delete')
    requests = relationship('Task', back_populates='user', cascade='save-update, merge, delete')

    def __repr__(self):
        res = f'<User: {self.id}'
        if self.is_admin:
            res += ' | admin'
        res += '>'

        return res


class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(256), nullable=False)
    clas = Column(String(4), nullable=False)
    parent_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    parent = relationship('User', back_populates='children')

    def __repr__(self):
        return f'<Student: {self.id}>'


class TaskType(Base):
    __tablename__ = 'tasks_types'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True)

    def __repr__(self):
        return f'<TaskType: {self.name}>'


class Service(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), unique=True)

    def __repr__(self):
        return f'<Service: {self.name}>'


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey('users.id'))
    type_id = Column(Integer, ForeignKey('tasks_types.id'))
    student_id = Column(ForeignKey('students.id'))

    student_beneficiary = Column(Boolean(), nullable=True)
    duration_in_month = Column(Integer, nullable=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=True)

    student = relationship('Student')
    type = relationship('TaskType')
    user = relationship('User')
    service = relationship('Service')

    def __repr__(self):
        return f'<Task: {self.id}>'


if __name__ == '__main__':
    engine = create_engine('sqlite:///../bot.db')
    Base.metadata.create_all(engine)

    s = sessionmaker(bind=engine)()
    s.add_all([
        TaskType(name='Справка об обучении в школе'),
        TaskType(name='Справка о питании'),
        TaskType(name='Спарвка о дополнительных услугах')
    ])
    s.commit()
    s.close()
    print('Database has been created')
