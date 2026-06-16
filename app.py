from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from flask_bcrypt import Bcrypt

from datetime import datetime
import os

# =====================================================
# APP
# =====================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "studybeat_secret_key_2026"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" +
    os.path.join(BASE_DIR, "studybeat.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

# =====================================================
# LOGIN MANAGER
# =====================================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = (
    "Debes iniciar sesión para acceder."
)

login_manager.login_message_category = "danger"

# =====================================================
# MODELOS
# =====================================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    tasks = db.relationship(
        "Task",
        backref="user",
        lazy=True,
        cascade="all, delete"
    )

    grades = db.relationship(
        "Grade",
        backref="user",
        lazy=True,
        cascade="all, delete"
    )

    goals = db.relationship(
        "Goal",
        backref="user",
        lazy=True,
        cascade="all, delete"
    )


class Task(db.Model):

    __tablename__ = "tasks"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    due_date = db.Column(
        db.String(50)
    )

    priority = db.Column(
        db.String(50)
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )


class Grade(db.Model):

    __tablename__ = "grades"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    subject = db.Column(
        db.String(150),
        nullable=False
    )

    score = db.Column(
        db.Float,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )


class Goal(db.Model):

    __tablename__ = "goals"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    progress = db.Column(
        db.Integer,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

# =====================================================
# USER LOADER
# =====================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    if current_user.is_authenticated:
        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "index.html"
    )

# =====================================================
# REGISTER
# =====================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        email = request.form.get(
            "email"
        )

        password = request.form.get(
            "password"
        )

        user_exists = User.query.filter_by(
            email=email
        ).first()

        if user_exists:

            flash(
                "Ese correo ya existe.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        hashed_password = (
            bcrypt.generate_password_hash(
                password
            ).decode("utf-8")
        )

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)

        db.session.commit()

        flash(
            "Cuenta creada correctamente.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "auth/register.html"
    )

# =====================================================
# LOGIN
# =====================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email"
        )

        password = request.form.get(
            "password"
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if (
            user and
            bcrypt.check_password_hash(
                user.password,
                password
            )
        ):

            login_user(user)

            flash(
                "Bienvenido a StudyBeat",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Correo o contraseña incorrectos.",
            "danger"
        )

    return render_template(
        "auth/login.html"
    )

# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Sesión cerrada.",
        "success"
    )

    return redirect(
        url_for("login")
    )# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
@login_required
def dashboard():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()

    grades = Grade.query.filter_by(
        user_id=current_user.id
    ).all()

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).all()

    pending_tasks = len(
        [task for task in tasks if not task.completed]
    )

    completed_tasks = len(
        [task for task in tasks if task.completed]
    )

    active_goals = len(goals)

    subjects = len(grades)

    average = 0

    if grades:

        average = round(
            sum(
                grade.score
                for grade in grades
            ) / len(grades),
            2
        )

    return render_template(
        "dashboard/dashboard.html",
        tasks=tasks,
        grades=grades,
        goals=goals,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        active_goals=active_goals,
        subjects=subjects,
        average=average
    )

# =====================================================
# TASKS
# =====================================================

@app.route("/tasks")
@login_required
def tasks():

    user_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Task.id.desc()
    ).all()

    return render_template(
        "tasks/tasks.html",
        tasks=user_tasks
    )

# =====================================================
# ADD TASK
# =====================================================

@app.route(
    "/task/add",
    methods=["POST"]
)
@login_required
def add_task():

    title = request.form.get("title")
    description = request.form.get("description")
    due_date = request.form.get("due_date")
    priority = request.form.get("priority")

    task = Task(
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
        user_id=current_user.id
    )

    db.session.add(task)

    db.session.commit()

    flash(
        "Tarea creada correctamente.",
        "success"
    )

    return redirect(
        url_for("tasks")
    )

# =====================================================
# COMPLETE TASK
# =====================================================

@app.route("/task/complete/<int:id>")
@login_required
def complete_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("tasks")
        )

    task.completed = not task.completed

    db.session.commit()

    flash(
        "Estado actualizado.",
        "success"
    )

    return redirect(
        url_for("tasks")
    )

# =====================================================
# DELETE TASK
# =====================================================

@app.route("/task/delete/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("tasks")
        )

    db.session.delete(task)

    db.session.commit()

    flash(
        "Tarea eliminada.",
        "success"
    )

    return redirect(
        url_for("tasks")
    )

# =====================================================
# EDIT TASK
# =====================================================

@app.route(
    "/task/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("tasks")
        )

    if request.method == "POST":

        task.title = request.form.get(
            "title"
        )

        task.description = request.form.get(
            "description"
        )

        task.due_date = request.form.get(
            "due_date"
        )

        task.priority = request.form.get(
            "priority"
        )

        db.session.commit()

        flash(
            "Tarea actualizada.",
            "success"
        )

        return redirect(
            url_for("tasks")
        )

    return render_template(
        "tasks/edit_task.html",
        task=task
    )

# =====================================================
# GRADES
# =====================================================

@app.route("/grades")
@login_required
def grades():

    grades = Grade.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Grade.id.desc()
    ).all()

    average = 0

    if grades:

        average = round(
            sum(
                grade.score
                for grade in grades
            ) / len(grades),
            2
        )

    return render_template(
        "grades/grades.html",
        grades=grades,
        average=average
    )

# =====================================================
# ADD GRADE
# =====================================================

@app.route(
    "/grade/add",
    methods=["POST"]
)
@login_required
def add_grade():

    subject = request.form.get(
        "subject"
    )

    score = float(
        request.form.get("score")
    )

    grade = Grade(
        subject=subject,
        score=score,
        user_id=current_user.id
    )

    db.session.add(grade)

    db.session.commit()

    flash(
        "Calificación agregada.",
        "success"
    )

    return redirect(
        url_for("grades")
    )

# =====================================================
# DELETE GRADE
# =====================================================

@app.route("/grade/delete/<int:id>")
@login_required
def delete_grade(id):

    grade = Grade.query.get_or_404(id)

    if grade.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("grades")
        )

    db.session.delete(grade)

    db.session.commit()

    flash(
        "Calificación eliminada.",
        "success"
    )

    return redirect(
        url_for("grades")
    )

# =====================================================
# EDIT GRADE
# =====================================================

@app.route(
    "/grade/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_grade(id):

    grade = Grade.query.get_or_404(id)

    if grade.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("grades")
        )

    if request.method == "POST":

        grade.subject = request.form.get(
            "subject"
        )

        grade.score = float(
            request.form.get("score")
        )

        db.session.commit()

        flash(
            "Calificación actualizada.",
            "success"
        )

        return redirect(
            url_for("grades")
        )

    return render_template(
        "grades/edit_grade.html",
        grade=grade
    )# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
@login_required
def dashboard():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()

    grades = Grade.query.filter_by(
        user_id=current_user.id
    ).all()

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).all()

    pending_tasks = len(
        [task for task in tasks if not task.completed]
    )

    completed_tasks = len(
        [task for task in tasks if task.completed]
    )

    active_goals = len(goals)

    subjects = len(grades)

    average = 0

    if grades:

        average = round(
            sum(
                grade.score
                for grade in grades
            ) / len(grades),
            2
        )

    return render_template(
        "dashboard/dashboard.html",
        tasks=tasks,
        grades=grades,
        goals=goals,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        active_goals=active_goals,
        subjects=subjects,
        average=average
    )

# =====================================================
# TASKS
# =====================================================

@app.route("/tasks")
@login_required
def tasks():

    user_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Task.id.desc()
    ).all()

    return render_template(
        "tasks/tasks.html",
        tasks=user_tasks
    )

# =====================================================
# ADD TASK
# =====================================================

@app.route(
    "/task/add",
    methods=["POST"]
)
@login_required
def add_task():

    title = request.form.get("title")
    description = request.form.get("description")
    due_date = request.form.get("due_date")
    priority = request.form.get("priority")

    task = Task(
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
        user_id=current_user.id
    )

    db.session.add(task)

    db.session.commit()

    flash(
        "Tarea creada correctamente.",
        "success"
    )

    return redirect(
        url_for("tasks")
    )

# =====================================================
# COMPLETE TASK
# =====================================================

@app.route("/task/complete/<int:id>")
@login_required
def complete_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("tasks")
        )

    task.completed = not task.completed

    db.session.commit()

    flash(
        "Estado actualizado.",
        "success"
    )

    return redirect(
        url_for("tasks")
    )

# =====================================================
# DELETE TASK
# =====================================================

@app.route("/task/delete/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("tasks")
        )

    db.session.delete(task)

    db.session.commit()

    flash(
        "Tarea eliminada.",
        "success"
    )

    return redirect(
        url_for("tasks")
    )

# =====================================================
# EDIT TASK
# =====================================================

@app.route(
    "/task/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("tasks")
        )

    if request.method == "POST":

        task.title = request.form.get(
            "title"
        )

        task.description = request.form.get(
            "description"
        )

        task.due_date = request.form.get(
            "due_date"
        )

        task.priority = request.form.get(
            "priority"
        )

        db.session.commit()

        flash(
            "Tarea actualizada.",
            "success"
        )

        return redirect(
            url_for("tasks")
        )

    return render_template(
        "tasks/edit_task.html",
        task=task
    )

# =====================================================
# GRADES
# =====================================================

@app.route("/grades")
@login_required
def grades():

    grades = Grade.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Grade.id.desc()
    ).all()

    average = 0

    if grades:

        average = round(
            sum(
                grade.score
                for grade in grades
            ) / len(grades),
            2
        )

    return render_template(
        "grades/grades.html",
        grades=grades,
        average=average
    )

# =====================================================
# ADD GRADE
# =====================================================

@app.route(
    "/grade/add",
    methods=["POST"]
)
@login_required
def add_grade():

    subject = request.form.get(
        "subject"
    )

    score = float(
        request.form.get("score")
    )

    grade = Grade(
        subject=subject,
        score=score,
        user_id=current_user.id
    )

    db.session.add(grade)

    db.session.commit()

    flash(
        "Calificación agregada.",
        "success"
    )

    return redirect(
        url_for("grades")
    )

# =====================================================
# DELETE GRADE
# =====================================================

@app.route("/grade/delete/<int:id>")
@login_required
def delete_grade(id):

    grade = Grade.query.get_or_404(id)

    if grade.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("grades")
        )

    db.session.delete(grade)

    db.session.commit()

    flash(
        "Calificación eliminada.",
        "success"
    )

    return redirect(
        url_for("grades")
    )

# =====================================================
# EDIT GRADE
# =====================================================

@app.route(
    "/grade/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_grade(id):

    grade = Grade.query.get_or_404(id)

    if grade.user_id != current_user.id:

        flash(
            "Acceso denegado.",
            "danger"
        )

        return redirect(
            url_for("grades")
        )

    if request.method == "POST":

        grade.subject = request.form.get(
            "subject"
        )

        grade.score = float(
            request.form.get("score")
        )

        db.session.commit()

        flash(
            "Calificación actualizada.",
            "success"
        )

        return redirect(
            url_for("grades")
        )

    return render_template(
        "grades/edit_grade.html",
        grade=grade
    )
