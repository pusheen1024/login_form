from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash

from data import db_session
from data.users import User
from login_form import LoginForm, RegistrationForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
db_session.global_init('database.db')
db_sess = db_session.create_session()


@login_manager.user_loader
def load_user(user_id):
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    return render_template('base.html', title='Главная страница')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit(): 
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', message='Неправильный логин или пароль', form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    fields = ['email', 'password', 'password_again', 'surname', 'name', 'position', 'speciality', 'address']
    params = {'title': 'Регистрация',
              'fields': fields,
              'form': form,
              'message': ''}
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            params['message'] = 'Пароли не совпадают'
        elif db_sess.query(User).filter(User.email == form.email.data).first():
            params['message'] = 'Такой пользователь уже есть'
        else:
            user_params = {field: getattr(form, field).data for field in fields if 'password' not in field}
            user_params['hashed_password'] = generate_password_hash(form.password.data)
            user = User(**user_params)
            db_sess.add(user)
            db_sess.commit()
            return redirect('/')
    return render_template('register.html', **params)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
