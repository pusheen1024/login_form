from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash

from data import db_session
from data.users import User
from data.jobs import Jobs
from data.departments import Departments
from login_form import LoginForm, RegistrationForm
from add_job import JobsForm
from add_department import DepartmentsForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
db_session.global_init('db/mars.db')
db_sess = db_session.create_session()


@login_manager.user_loader
def load_user(user_id):
    return db_sess.query(User).get(user_id)


@app.route('/jobs')
@login_required
def jobs():
    jobs = list()
    for item in db_sess.query(Jobs).all():
        item_dict = item.to_dict()
        job = dict()
        job['Title of activity'] = item_dict['job']
        leader = db_sess.query(User).filter(User.id == item_dict['team_leader']).first().to_dict()
        job['Team leader'] = f"{leader['name']} {leader['surname']}"
        job['Duration'] = f"{item_dict['work_size']} hours"
        job['List of collaborators'] = item_dict['collaborators']
        job['Is finished'] = ['Is not finished', 'Is finished'][item_dict['is_finished']]
        can_edit = current_user.id in (1, item_dict['team_leader'])
        jobs.append((job, item_dict['id'], can_edit))
    return render_template('journal.html', jobs=jobs)


@app.route('/departments', methods=['GET', 'POST'])
@login_required
def departments():
    departments = list()
    for item in db_sess.query(Departments).all():
        item_dict = item.to_dict()
        department = dict()
        department['Title of department'] = item_dict['title']
        chief = db_sess.query(User).filter(User.id == item_dict['chief']).first().to_dict()
        department['Chief'] = f"{chief['name']} {chief['surname']}"
        department['Members'] = item_dict['members']
        department['Department Email'] = item_dict['email']
        can_edit = current_user.id in (1, item_dict['chief'])
        departments.append((department, item_dict['id'], can_edit))
    return render_template('departments.html', jobs=departments)


@app.route('/')
def index():
    return render_template('base.html', title='Главная страница')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/jobs')
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
            return redirect('/jobs')
    return render_template('register.html', **params)


@app.route('/add_job', methods=['GET', 'POST'])
@login_required
def add_job():
    form = JobsForm()
    fields = ['job', 'team_leader', 'work_size', 'collaborators']
    params = {'title': 'Добавление работы',
              'fields': fields,
              'form': form,
              'text': 'Adding a job'}
    if form.validate_on_submit():
        job_params = {field: getattr(form, field).data for field in fields}
        job_params['is_finished'] = form.is_finished.data
        job = Jobs(**job_params)
        db_sess.add(job)
        db_sess.commit()
        return redirect('/jobs')
    return render_template('add_entry.html', **params)


@app.route('/edit_job/<int:jobs_id>', methods=['GET', 'POST'])
@login_required
def edit_job(jobs_id):
    job = db_sess.query(Jobs).get(jobs_id)
    if current_user.id not in (1, job.team_leader):
        return render_template('error.html', message='Access denied')
    form = JobsForm()
    fields = ['job', 'team_leader', 'work_size', 'collaborators']
    params = {'title': 'Добавление работы',
              'fields': fields,
              'form': form,
              'text': 'Editing a job'}
    if form.validate_on_submit():
        for field in fields:
            setattr(job, field, getattr(form, field).data)
        db_sess.commit()
        return redirect('/jobs')
    else:
        for field in fields:
            setattr(getattr(form, field), 'data', getattr(job, field))      
        return render_template('add_entry.html', **params)


@app.route('/delete_job/<int:jobs_id>', methods=['GET', 'POST'])
@login_required
def delete_job(jobs_id):
    job = db_sess.query(Jobs).get(jobs_id)
    if current_user.id not in (1, job.team_leader):
        return render_template('error.html', message='Access denied')
    db_sess.delete(job)
    db_sess.commit()
    return redirect('/')


@app.route('/add_department', methods=['GET', 'POST'])
@login_required
def add_department():
    form = DepartmentsForm()
    fields = ['title', 'chief', 'members', 'email']
    params = {'title': 'Добавление департамента',
              'fields': fields,
              'form': form,
              'text': 'Adding a department'}
    if form.validate_on_submit():
        department_params = {field: getattr(form, field).data for field in fields}
        department = Departments(**department_params)
        db_sess.add(department)
        db_sess.commit()
        return redirect('/departments')
    return render_template('add_entry.html', **params)


@app.route('/edit_department/<int:department_id>', methods=['GET', 'POST'])
@login_required
def edit_department(department_id):
    department = db_sess.query(Departments).get(department_id)
    form = DepartmentsForm()
    fields = ['title', 'chief', 'members', 'email']
    params = {'title': 'Добавление департамента',
              'fields': fields,
              'form': form,
              'text': 'Editing a department'}
    if form.validate_on_submit():
        for field in fields:
            setattr(department, field, getattr(form, field).data)
        db_sess.commit()
        return redirect('/departments')
    else:
        for field in fields:
            setattr(getattr(form, field), 'data', getattr(department, field))      
        return render_template('add_entry.html', **params)


@app.route('/delete_department/<int:department_id>', methods=['GET', 'POST'])
@login_required
def delete_department(department_id):
    department = db_sess.query(Departments).get(department_id)
    db_sess.delete(department)
    db_sess.commit()
    return redirect('/departments')


@app.errorhandler(401)
def unauthorized(error):
    return render_template('error.html', message='Unauthorized')


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', message='Not found')


@app.errorhandler(500)
def not_found(error):
    return render_template('error.html', message='Internal server error')


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
