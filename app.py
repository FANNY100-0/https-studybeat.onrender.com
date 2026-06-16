from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from flask_bcrypt import Bcrypt

from datetime import datetime

import os

# =====================================================
# CONFIGURACIÓN
# =====================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "studybeat_secret"
)

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:

    BASE_DIR = os.path.abspath(
        os.path.dirname(__file__)
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" +
        os.path.join(
            BASE_DIR,
            "studybeat.db"
        )
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
    "Debes iniciar sesión."
)

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
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
    )

    grades = db.relationship(
        "Grade",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
    )

    goals = db.relationship(
        "Goal",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
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
        db.ForeignKey("users.id")
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
        db.ForeignKey("users.id")
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
        db.ForeignKey("users.id")
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

        user = User.query.filter_by(
            email=email
        ).first()

        if user:

            flash(
                "El correo ya existe.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

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
        "register.html"
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

        if user and bcrypt.check_password_hash(
            user.password,
            password
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
            "Credenciales incorrectas",
            "danger"
        )

    return render_template(
        "login.html"
    )

# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

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

    pending_tasks = len([
        t for t in tasks
        if not t.completed
    ])

    completed_tasks = len([
        t for t in tasks
        if t.completed
    ])

    average = 0

    if grades:

        average = round(
            sum(
                grade.score
                for grade in grades
            ) / len(grades),
            2
        )

    productivity = 0

    if len(tasks) > 0:

        productivity = round(
            (completed_tasks / len(tasks))
            * 100,
            1
        )

    return render_template(
        "dashboard.html",
        tasks=tasks[:5],
        grades=grades[:5],
        goals=goals[:5],
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        average=average,
        active_goals=len(goals),
        subjects=len(grades),
        productivity=productivity
    )

# =====================================================
# API ESTADÍSTICAS
# =====================================================

@app.route("/api/stats")
@login_required
def api_stats():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()

    grades = Grade.query.filter_by(
        user_id=current_user.id
    ).all()

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).all()

    pending = len([
        t for t in tasks
        if not t.completed
    ])

    completed = len([
        t for t in tasks
        if t.completed
    ])

    average = 0

    if grades:

        average = round(
            sum(
                g.score
                for g in grades
            ) / len(grades),
            2
        )

    productivity = 0

    if len(tasks) > 0:

        productivity = round(
            (completed / len(tasks))
            * 100,
            1
        )

    return jsonify({

        "average": average,

        "pending_tasks": pending,

        "completed_tasks": completed,

        "goals": len(goals),

        "productivity": productivity

    })

# =====================================================
# LISTA DE TAREAS
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
        "tareas.html",
        tasks=user_tasks
    )

# =====================================================
# CREAR TAREA
# =====================================================

@app.route(
    "/task/add",
    methods=["POST"]
)
@login_required
def add_task():

    title = request.form.get(
        "title"
    )

    description = request.form.get(
        "description"
    )

    due_date = request.form.get(
        "due_date"
    )

    priority = request.form.get(
        "priority"
    )

    if not title:

        flash(
            "El título es obligatorio.",
            "danger"
        )

        return redirect(
            url_for("tasks")
        )

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
# EDITAR TAREA
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
        "edit_task.html",
        task=task
    )

# =====================================================
# COMPLETAR TAREA
# =====================================================

@app.route(
    "/task/complete/<int:id>"
)
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
# ELIMINAR TAREA
# =====================================================

@app.route(
    "/task/delete/<int:id>"
)
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

    pending_tasks = len([
        t for t in tasks
        if not t.completed
    ])

    completed_tasks = len([
        t for t in tasks
        if t.completed
    ])

    average = 0

    if grades:

        average = round(
            sum(
                grade.score
                for grade in grades
            ) / len(grades),
            2
        )

    productivity = 0

    if len(tasks) > 0:

        productivity = round(
            (completed_tasks / len(tasks))
            * 100,
            1
        )

    return render_template(
        "dashboard.html",
        tasks=tasks[:5],
        grades=grades[:5],
        goals=goals[:5],
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        average=average,
        active_goals=len(goals),
        subjects=len(grades),
        productivity=productivity
    )

# =====================================================
# API ESTADÍSTICAS
# =====================================================

@app.route("/api/stats")
@login_required
def api_stats():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()

    grades = Grade.query.filter_by(
        user_id=current_user.id
    ).all()

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).all()

    pending = len([
        t for t in tasks
        if not t.completed
    ])

    completed = len([
        t for t in tasks
        if t.completed
    ])

    average = 0

    if grades:

        average = round(
            sum(
                g.score
                for g in grades
            ) / len(grades),
            2
        )

    productivity = 0

    if len(tasks) > 0:

        productivity = round(
            (completed / len(tasks))
            * 100,
            1
        )

    return jsonify({

        "average": average,

        "pending_tasks": pending,

        "completed_tasks": completed,

        "goals": len(goals),

        "productivity": productivity

    })

# =====================================================
# LISTA DE TAREAS
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
        "tareas.html",
        tasks=user_tasks
    )

# =====================================================
# CREAR TAREA
# =====================================================

@app.route(
    "/task/add",
    methods=["POST"]
)
@login_required
def add_task():

    title = request.form.get(
        "title"
    )

    description = request.form.get(
        "description"
    )

    due_date = request.form.get(
        "due_date"
    )

    priority = request.form.get(
        "priority"
    )

    if not title:

        flash(
            "El título es obligatorio.",
            "danger"
        )

        return redirect(
            url_for("tasks")
        )

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
# EDITAR TAREA
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
        "edit_task.html",
        task=task
    )

# =====================================================
# COMPLETAR TAREA
# =====================================================

@app.route(
    "/task/complete/<int:id>"
)
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
# ELIMINAR TAREA
# =====================================================

@app.route(
    "/task/delete/<int:id>"
)
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
    )# =====================================================
# CALIFICACIONES
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

    highest_grade = 0

    lowest_grade = 0

    if grades:

        scores = [
            g.score
            for g in grades
        ]

        average = round(
            sum(scores) / len(scores),
            2
        )

        highest_grade = max(scores)

        lowest_grade = min(scores)

    return render_template(
        "calificacion.html",
        grades=grades,
        average=average,
        highest_grade=highest_grade,
        lowest_grade=lowest_grade
    )

# =====================================================
# AGREGAR CALIFICACIÓN
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

    score = request.form.get(
        "score"
    )

    if not subject or not score:

        flash(
            "Completa todos los campos.",
            "danger"
        )

        return redirect(
            url_for("grades")
        )

    grade = Grade(

        subject=subject,

        score=float(score),

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
# EDITAR CALIFICACIÓN
# =====================================================

@app.route(
    "/grade/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_grade(id):

    grade = Grade.query.get_or_404(id)

    if grade.user_id != current_user.id:

        return redirect(
            url_for("grades")
        )

    if request.method == "POST":

        grade.subject = request.form.get(
            "subject"
        )

        grade.score = float(
            request.form.get(
                "score"
            )
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
        "edit_grade.html",
        grade=grade
    )

# =====================================================
# ELIMINAR CALIFICACIÓN
# =====================================================

@app.route(
    "/grade/delete/<int:id>"
)
@login_required
def delete_grade(id):

    grade = Grade.query.get_or_404(id)

    if grade.user_id != current_user.id:

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
# METAS
# =====================================================

@app.route("/goals")
@login_required
def goals():

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Goal.id.desc()
    ).all()

    return render_template(
        "metas.html",
        goals=goals
    )

# =====================================================
# CREAR META
# =====================================================

@app.route(
    "/goal/add",
    methods=["POST"]
)
@login_required
def add_goal():

    title = request.form.get(
        "title"
    )

    progress = request.form.get(
        "progress",
        0
    )

    goal = Goal(

        title=title,

        progress=int(progress),

        user_id=current_user.id

    )

    db.session.add(goal)

    db.session.commit()

    flash(
        "Meta creada.",
        "success"
    )

    return redirect(
        url_for("goals")
    )

# =====================================================
# EDITAR META
# =====================================================

@app.route(
    "/goal/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_goal(id):

    goal = Goal.query.get_or_404(id)

    if goal.user_id != current_user.id:

        return redirect(
            url_for("goals")
        )

    if request.method == "POST":

        goal.title = request.form.get(
            "title"
        )

        goal.progress = int(
            request.form.get(
                "progress"
            )
        )

        db.session.commit()

        flash(
            "Meta actualizada.",
            "success"
        )

        return redirect(
            url_for("goals")
        )

    return render_template(
        "edit_goal.html",
        goal=goal
    )

# =====================================================
# ACTUALIZAR PROGRESO
# =====================================================

@app.route(
    "/goal/update/<int:id>",
    methods=["POST"]
)
@login_required
def update_goal(id):

    goal = Goal.query.get_or_404(id)

    if goal.user_id != current_user.id:

        return redirect(
            url_for("goals")
        )

    progress = int(
        request.form.get(
            "progress"
        )
    )

    if progress < 0:
        progress = 0

    if progress > 100:
        progress = 100

    goal.progress = progress

    db.session.commit()

    flash(
        "Progreso actualizado.",
        "success"
    )

    return redirect(
        url_for("goals")
    )

# =====================================================
# ELIMINAR META
# =====================================================

@app.route(
    "/goal/delete/<int:id>"
)
@login_required
def delete_goal(id):

    goal = Goal.query.get_or_404(id)

    if goal.user_id != current_user.id:

        return redirect(
            url_for("goals")
        )

    db.session.delete(goal)

    db.session.commit()

    flash(
        "Meta eliminada.",
        "success"
    )

    return redirect(
        url_for("goals")
    )

# =====================================================
# BUSCADOR GLOBAL
# =====================================================

@app.route("/search")
@login_required
def search():

    query = request.args.get(
        "q",
        ""
    )

    task_results = Task.query.filter(
        Task.user_id == current_user.id,
        Task.title.contains(query)
    ).all()

    grade_results = Grade.query.filter(
        Grade.user_id == current_user.id,
        Grade.subject.contains(query)
    ).all()

    goal_results = Goal.query.filter(
        Goal.user_id == current_user.id,
        Goal.title.contains(query)
    ).all()

    return render_template(
        "search.html",
        query=query,
        tasks=task_results,
        grades=grade_results,
        goals=goal_results
    )
