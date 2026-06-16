from flask import Flask, render_template, request, redirect, url_for, flash
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

app = Flask(__name__)

app.config["SECRET_KEY"] = "studybeat_secret"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" +
    os.path.join(BASE_DIR, "studybeat.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# =====================================================
# MODELOS
# =====================================================

class User(UserMixin, db.Model):

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


class Task(db.Model):

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

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


class Grade(db.Model):

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

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


class Goal(db.Model):

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

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user:

            flash(
                "Correo ya registrado",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        hashed = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        new_user = User(
            username=username,
            email=email,
            password=hashed
        )

        db.session.add(new_user)
        db.session.commit()

        flash(
            "Cuenta creada correctamente",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and bcrypt.check_password_hash(
            user.password,
            password
        ):

            login_user(user)

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

    pending_tasks = len(
        [t for t in tasks if not t.completed]
    )

    average = 0

    if grades:

        average = round(
            sum(
                g.score for g in grades
            ) / len(grades),
            2
        )

    return render_template(
        "dashboard.html",
        tasks=tasks,
        grades=grades,
        goals=goals,
        pending_tasks=pending_tasks,
        average=average,
        active_goals=len(goals),
        subjects=len(grades)
    )

# =====================================================
# TAREAS
# =====================================================

@app.route("/tasks")
@login_required
def tasks():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Task.id.desc()
    ).all()

    return render_template(
        "tareas.html",
        tasks=tasks
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

    task = Task(
        title=request.form.get("title"),
        description=request.form.get(
            "description"
        ),
        due_date=request.form.get(
            "due_date"
        ),
        priority=request.form.get(
            "priority"
        ),
        user_id=current_user.id
    )

    db.session.add(task)
    db.session.commit()

    flash(
        "Tarea agregada correctamente",
        "success"
    )

    return redirect(
        url_for("tasks")
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
            "Acceso denegado",
            "danger"
        )

        return redirect(
            url_for("tasks")
        )

    task.completed = not task.completed

    db.session.commit()

    flash(
        "Estado actualizado",
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

        return redirect(
            url_for("tasks")
        )

    db.session.delete(task)
    db.session.commit()

    flash(
        "Tarea eliminada",
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
            "Tarea actualizada",
            "success"
        )

        return redirect(
            url_for("tasks")
        )

    return redirect(
        url_for("tasks")
    )

# =====================================================
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

    if grades:

        average = round(
            sum(
                g.score for g in grades
            ) / len(grades),
            2
        )

    return render_template(
        "calificacion.html",
        grades=grades,
        average=average
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

    grade = Grade(
        subject=request.form.get(
            "subject"
        ),
        score=float(
            request.form.get("score")
        ),
        user_id=current_user.id
    )

    db.session.add(grade)
    db.session.commit()

    flash(
        "Calificación agregada",
        "success"
    )

    return redirect(
        url_for("grades")
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
        "Calificación eliminada",
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
            request.form.get("score")
        )

        db.session.commit()

        flash(
            "Calificación actualizada",
            "success"
        )

        return redirect(
            url_for("grades")
        )

    return redirect(
        url_for("grades")
    )# =====================================================
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

    title = request.form.get("title")

    progress = int(
        request.form.get(
            "progress",
            0
        )
    )

    goal = Goal(
        title=title,
        progress=progress,
        user_id=current_user.id
    )

    db.session.add(goal)
    db.session.commit()

    flash(
        "Meta creada correctamente",
        "success"
    )

    return redirect(
        url_for("goals")
    )

# =====================================================
# ACTUALIZAR META
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

    goal.progress = int(
        request.form.get(
            "progress"
        )
    )

    db.session.commit()

    flash(
        "Progreso actualizado",
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
            "Meta actualizada",
            "success"
        )

        return redirect(
            url_for("goals")
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
        "Meta eliminada",
        "success"
    )

    return redirect(
        url_for("goals")
    )

# =====================================================
# MÚSICA
# =====================================================

@app.route("/music")
@login_required
def music():

    playlists = [
        {
            "title": "LoFi Hip Hop",
            "youtube": "jfKfPfyJRdk"
        },
        {
            "title": "Piano Relajante",
            "youtube": "lFcSrYw-ARY"
        },
        {
            "title": "Música Instrumental",
            "youtube": "WPni755-Krg"
        },
        {
            "title": "Study Music",
            "youtube": "5qap5aO4i9A"
        }
    ]

    return render_template(
        "musica.html",
        playlists=playlists
    )

# =====================================================
# PERFIL
# =====================================================

@app.route("/profile")
@login_required
def profile():

    task_count = Task.query.filter_by(
        user_id=current_user.id
    ).count()

    grade_count = Grade.query.filter_by(
        user_id=current_user.id
    ).count()

    goal_count = Goal.query.filter_by(
        user_id=current_user.id
    ).count()

    grades = Grade.query.filter_by(
        user_id=current_user.id
    ).all()

    average = 0

    if grades:

        average = round(
            sum(
                g.score for g in grades
            ) / len(grades),
            2
        )

    return render_template(
        "perfil.html",
        user=current_user,
        task_count=task_count,
        grade_count=grade_count,
        goal_count=goal_count,
        average=average
    )

# =====================================================
# API ESTADÍSTICAS
# =====================================================

@app.route("/stats")
@login_required
def stats():

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
        [t for t in tasks if not t.completed]
    )

    completed_tasks = len(
        [t for t in tasks if t.completed]
    )

    average = 0

    if grades:

        average = round(
            sum(
                g.score for g in grades
            ) / len(grades),
            2
        )

    return {
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "average": average,
        "goals": len(goals)
    }

# =====================================================
# ERROR 404
# =====================================================

@app.errorhandler(404)
def page_not_found(error):

    return (
        render_template(
            "404.html"
        ),
        404
    )

# =====================================================
# ERROR 500
# =====================================================

@app.errorhandler(500)
def server_error(error):

    return (
        render_template(
            "500.html"
        ),
        500
    )

# =====================================================
# CREAR BASE DE DATOS
# =====================================================

with app.app_context():
    db.create_all()

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )
