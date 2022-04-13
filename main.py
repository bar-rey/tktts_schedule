import json, os, sqlite3, vk_config
from flask import Flask, request, redirect, url_for, render_template, abort, g, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, AdministratorRegisterForm, GuestRegisterForm, AddScheduleForm, VkBindForm, VkNotifyForm
from database import Database
from login import User
from schedule import Schedule
from vk_api.vk_api import VkApi
from vk_notifier import vk_notifier
from vk_event_handler import VkEventHandler

app = Flask(__name__)
with open(os.path.join(app.root_path, 'app_secret_key.txt'), mode='r', encoding='utf-8') as f:
	app.config['SECRET_KEY'] = f.read()
app.config['DATABASE'] = os.path.join(app.root_path, 'db.db')

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для просмотра страницы"
login_manager.login_message_category = "success"

def connect_db():
	'''
	Функция для установления соединения с базой данных.
	Данные при работе с БД будут предоставляться в формате ключ - значение (название поля - значение поля записи)
	'''
	conn = sqlite3.connect(app.config['DATABASE'])
	conn.row_factory = sqlite3.Row
	return conn

def create_db():
	'''
	Функция для создания базы данных и заполнения её данными по умолчанию с помощью скриптов
	'''
	db = connect_db()
	with open(os.path.join(app.root_path, 'database_scripts/script.sql'), mode='r', encoding='utf-8') as f:
		db.cursor().executescript(f.read())
	try:
		with open(os.path.join(app.root_path, 'database_scripts/ensure_admin.sql'), mode='r', encoding='utf-8') as f:
			db.cursor().executescript(f.read())
	except FileNotFoundError:
		print("File 'database_scripts/ensure_admin.sql' does not exist.\nCreate this script with admin password generated by werkzeug.security.generate_password_hash method and call create_db again.")
	db.commit()
	db.close()

def get_db():
	'''
	Функция для добавления в объект g подключения к БД
	'''
	if not hasattr(g, 'link_db'):
		g.link_db = connect_db()
	return g.link_db

def get_menu_category():
	'''
	Функция для получения категории меню
	default/guest/moderator/administrator
	'''
	return current_user.role if current_user.is_authenticated else "default"

dbase = None
@app.before_request
def before_request():
	'''
	Подключение к БД перед контекстом запроса
	'''
	global dbase
	db = get_db()
	dbase = Database(db)

@app.teardown_appcontext
def close_db(error):
	'''
	Функция для закрытия соединения с БД, если оно было установлено
	'''
	if hasattr(g, 'link_db'):
		g.link_db.close()

@login_manager.user_loader
def load_user(user_id):
	'''
	Загрузка пользователя
	user_id - извлечённый из сессионной куки id пользователя, полученный методом get_id класса User
	'''
	user = dbase.getUserById(user_id)
	return User().create(user) if user else abort(401)

@app.route("/register/", methods=["POST", "GET"])
def register():
	'''
	Создание нового аккаунта.
	Администратор может создавать сколько угодно новых аккаунтов, выбирая им роль (гость/модератор/администратор).
	Неавторизованный пользователь создаёт аккаунт, который будет иметь роль гостя.
	'''
	if current_user.is_authenticated:
		if current_user.role == "administrator":
			form = AdministratorRegisterForm()
			if form.validate_on_submit():
				if dbase.addUser(form.login.data, generate_password_hash(form.password.data), form.role.data):
					flash("Аккаунт зарегистрирован", "success")
				else:
					flash("Либо аккаунт с таким логином уже зарегистрирован, либо произошла ошибка на нашей стороне", "error")
				return redirect(url_for('register'))
			return render_template("register.html", title="Регистрация", form=form, menu=dbase.getMenu(category="administrator", exclude_url=request.path))
		else:
			return redirect(url_for('index'))
	else:
		form = GuestRegisterForm()
		if form.validate_on_submit():
			if dbase.addUser(form.login.data, generate_password_hash(form.password.data), role="guest"):
				flash("Аккаунт зарегистрирован. Теперь вы можете авторизоваться", "success")
				return redirect(url_for('login'))
			else:
				flash("Либо аккаунт с таким логином уже зарегистрирован, либо произошла ошибка на нашей стороне", "error")
				return redirect(url_for('register'))
		return render_template("register.html", title="Регистрация", form=form, menu=dbase.getMenu(category=get_menu_category(), exclude_url=request.path))

@app.route("/login/", methods=["POST", "GET"])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = dbase.getUserByLogin(form.login.data)    # получение данных пользователя из БД
		if user and check_password_hash(user['password'], form.password.data):    # проверка пароля
			userlogin = User().create(user)    # объект пользователя == запись из БД
			login_user(userlogin, remember=form.remember.data) # объект будет доступен через current_user; id объекта пользователя хранится в сессии
			return redirect(request.args.get("next") or url_for('index'))
		flash("Неверный логин или пароль", "error")
	return render_template("login.html", title="Авторизация", form=form, menu=dbase.getMenu(category="default", exclude_url=request.path))

@app.route('/logout/')
@login_required
def logout():
	logout_user()
	flash("Вы вышли из аккаунта", "success")
	return redirect(url_for('login'))

@app.route('/index')
@app.route('/')
def index():
    return render_template("index.html", title="Главная", menu=dbase.getMenu(category=get_menu_category()))

@app.route("/schedule/show/", methods=["POST", "GET"])
def schedule_show():
	cats_available_dates = Schedule.get_available_dates()
	cats = tuple(cats_available_dates.keys())
	schedules = {}
	lists = {}
	for cat in cats:
		schedules[cat] = {}
		lists[cat] = {}
		if cats_available_dates[cat]:
			for date in cats_available_dates[cat]:
				schedules[cat][date] = Schedule.get_schedule(cat, "all", date)
				lists[cat][date] = sorted(Schedule.get_list(cat, date))
		else: break
	return render_template("schedule_show.html", title="Расписание", lists_dict=lists, schedules_dict=schedules, dates_dict=Schedule.get_available_dates(),
						 menu=dbase.getMenu(category=get_menu_category(), exclude_url=request.path))

@app.route("/schedule/add/", methods=["POST", "GET"])
@login_required
def schedule_add():
	if current_user.role == "guest":
		abort(403)
	form = AddScheduleForm()
	if form.validate_on_submit():
		url = form.url.data
		res = Schedule.add_schedule(url)
		if res: flash("Расписание успешно добавлено", "success")
		elif res is None: flash("Неправильная ссылка", "error")
		else: flash("Что-то пошло не так", "error")
		return redirect(url_for("schedule_add"))
	return render_template("schedule_add.html", title="Добавление расписания", menu=dbase.getMenu(category=get_menu_category(), exclude_url=request.path), form=form)

@app.route("/vk/bind/", methods=["POST", "GET"])
@login_required
def vk_bind():
	if current_user.role == "guest":
		abort(403)
	form = VkBindForm()
	if form.validate_on_submit():
		url = form.url.data
		vk_session = VkApi(token=vk_config.access_token, version=vk_config.api_version)
		identifier = url.rsplit("/")[-1] or url.rsplit("/")[-2]
		vk_id = None
		# первая попытка получить user_id (vk.com/id123)
		try:
			vk_id = int(identifier[2::])
		except ValueError:
			# вторая попытка получить user_id (vk.com/shortname)
			data = vk_session.method('users.get', {'user_ids': identifier})
			if data:
				try:
					vk_id = data['response'][0]['id']
				except:
					flash("Неправильная ссылка", "error")
					return redirect(url_for("vk_bind"))
		if vk_id:
			if dbase.bindVk(vk_id, current_user.get_id()):
				flash("Страница успешно привязана", "success")
			else:
				flash("Произошла ошибка. Повторите попытку позже", "error")
		return redirect(url_for("vk_bind"))
	return render_template("vk_bind.html", title="Привязка страницы ВК", menu=dbase.getMenu(category=get_menu_category(), exclude_url=request.path), form=form)

@app.route("/vk/notify/", methods=["POST", "GET"])
@login_required
def vk_notify():
	if current_user.role == "guest":
		abort(403)
	form = VkNotifyForm()
	dates = Schedule.get_available_dates()[Schedule.groups_name]
	if dates:
		choices = []
		for i in range(len(dates)):
			choices.append((dates[i], dates[i]))
		form.date.choices = choices
	if form.validate_on_submit():
		date = form.date.data
		if date:
			subs = dbase.getSubscribers()
			if subs:
				flash(f"Рассылка расписания за {date} проведена успешно", "success") \
				if vk_notifier(Schedule.groups_name, {date,}, subs) else flash("Рассылка не удалась", "error")
			else:
				flash("Никто не подписан на рассылку", "error")
		else:
			flash("Дата не выбрана", "error")
		return redirect(url_for("vk_notify"))
	return render_template("vk_notify.html", title="Рассылка расписания", menu=dbase.getMenu(category=get_menu_category(), exclude_url=request.path), form=form)

@app.route("/vk/callback-api/", methods=["POST"])
def vk_callback_api():
    event = json.loads(request.data)
    return VkEventHandler(event, dbase).create_answer()

def error_404_json():
    return jsonify({"error": {"message": "not found", "status_code": "404"}})

def error_422_json():
    return jsonify({"error": {"message": "missing params", "status_code": "422"}})


if __name__ == "__main__":
    app.run(host='0.0.0.0')
