"""
Инициализация и управление сессией SQLAlchemy для приложения GeoTravel.
Обеспечивает глобальный доступ к движку и фабрике сессий.
"""

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

SqlAlchemyBase = orm.declarative_base()

__factory = None  # Фабрика сессий, инициализируется один раз через global_init


def global_init(db_file: str):
    """
    Создаёт SQLAlchemy engine и фабрику сессий.
    Вызывается один раз при запуске приложения из main.py.
    """
    global __factory
    if __factory:
        return  # Уже инициализировано — выходим
    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")
    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)
    from . import models
    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    """Создаёт и возвращает новую сессию для работы с БД."""
    global __factory
    return __factory()
