from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo

class AdministratorRegisterForm(FlaskForm):
	login = StringField("Логин: ", validators=[DataRequired(), Length(min=1, max=50, message="Логин должен содержать от 1 до 50 символов")], render_kw={"placeholder": "Логин"})
	password = PasswordField("Пароль: ", validators=[DataRequired(), Length(min=6, max=30, message="Пароль должен содержать от 6 до 30 символов")], render_kw={"placeholder": "Пароль"})
	password_repeat = PasswordField("Повторите пароль: ", validators=[DataRequired(), EqualTo('password', message="Пароли не совпадают")], render_kw={"placeholder": "Повтор пароля"})
	role = SelectField("Роль", choices=[('guest', 'Гость'), ('moderator', 'Модератор'), ('administrator', 'Администратор')], validators=[DataRequired()])
	submit = SubmitField("Регистрация")

class GuestRegisterForm(FlaskForm):
	login = StringField("Логин: ", validators=[DataRequired(), Length(min=1, max=50, message="Логин должен содержать от 1 до 50 символов")], render_kw={"placeholder": "Логин"})
	password = PasswordField("Пароль: ", validators=[DataRequired(), Length(min=6, max=30, message="Пароль должен содержать от 6 до 30 символов")], render_kw={"placeholder": "Пароль"})
	password_repeat = PasswordField("Повторите пароль: ", validators=[DataRequired(), EqualTo('password', message="Пароли не совпадают")], render_kw={"placeholder": "Повтор пароля"})
	submit = SubmitField("Регистрация")

class LoginForm(FlaskForm):
	login = StringField("Логин: ", validators=[DataRequired(), Length(min=1, max=50, message="Логин должен содержать от 1 до 50 символов")], render_kw={"placeholder": "Логин"})
	password = PasswordField("Пароль: ", validators=[DataRequired(), Length(min=6, max=30, message="Пароль должен иметь длину от 6 до 30 символов")], render_kw={"placeholder": "Пароль"})
	remember = BooleanField("Запомнить меня", default = False)
	submit = SubmitField("Войти")
    
class AddScheduleForm(FlaskForm):
	url = StringField("Ссылка: ", validators=[DataRequired(), Length(min=30, max=200, message="Ссылка слишком короткая/длинная")], render_kw={"placeholder": "Ссылка на расписание"})
	submit = SubmitField("Добавить расписание")

class VkBindForm(FlaskForm):
    url = StringField("Ссылка: ", validators=[DataRequired()], render_kw={"placeholder": "Ссылка на страницу ВК"})
    submit = SubmitField("Привязать страницу ВК")

class VkNotifyForm(FlaskForm):
	date = SelectField("Дата", choices=[("", "Список дат")], validators=[DataRequired()])
	submit = SubmitField("Уведомить")