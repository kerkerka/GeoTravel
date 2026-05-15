"""
Формы для регистрации и авторизации пользователей (WTF-Forms).
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, EmailField
from wtforms.validators import DataRequired, EqualTo, Length


class RegisterForm(FlaskForm):
    """Форма регистрации: почта, пароль (с подтверждением), имя, описание."""
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password', message="Пароли не совпадают")])
    name = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=30)])
    about = TextAreaField("О себе")
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    """Форма входа: почта и пароль."""
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = StringField('Запомнить меня')
    submit = SubmitField('Войти')
