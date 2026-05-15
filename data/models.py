"""
ORM-модели для GeoTravel:
- User — аккаунт пользователя (аутентификация, профиль)
- Trip — путешествие/маршрут, принадлежит пользователю
- Stop — точка маршрута (город, достопримечательность) с координатами и фото
"""

import datetime
import sqlalchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from data.db_session import SqlAlchemyBase
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin):
    """Модель пользователя. Хранит данные профиля и хеш пароля."""
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    avatar_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    trips = relationship("Trip", back_populates='user')

    def set_password(self, password: str):
        """Сохраняет хеш пароля (никогда не хранит открытый пароль)."""
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Проверяет введённый пароль против сохранённого хеша."""
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f"<User> {self.id} {self.name} {self.email}"


class Trip(SqlAlchemyBase):
    """Модель путешествия. Содержит заголовок, описание, дату создания и список остановок."""
    __tablename__ = 'trips'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = relationship('User', back_populates='trips')
    stops = relationship("Stop", back_populates='trip', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Trip> {self.id} '{self.title}'"


class Stop(SqlAlchemyBase):
    """Остановка маршрута: название, адрес, гео-координаты, фото."""
    __tablename__ = 'stops'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    address = sqlalchemy.Column(sqlalchemy.String)
    latitude = sqlalchemy.Column(sqlalchemy.Float)
    longitude = sqlalchemy.Column(sqlalchemy.Float)
    photo_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    trip_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("trips.id"))
    trip = relationship('Trip', back_populates='stops')

    def __repr__(self):
        return f"<Stop> '{self.name}' at ({self.latitude}, {self.longitude})"
