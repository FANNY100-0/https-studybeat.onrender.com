from flask import Flask, render_template, redirect, url_for, request, flash
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

app.config["SECRET_KEY"] = "studybeat_secret_key"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = \
    "sqlite:///" + os.path.join(BASE_DIR, "studybeat.db")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ==================================================
# MODELOS
# ==================================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

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


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)

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
        db.ForeignKey("users.id"),
        nullable=False
    )


class Grade(db.Model):
    __tablename__ = "grades"

    id = db.Column(db.Integer, primary_key=True)

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
        db.ForeignKey("users.id"),
        nullable=False
    )


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)

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
        db.ForeignKey("users.id"),
        nullable=False
    )


# ==================================================
# LOGIN MANAGER
# ==================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


# ==================================================
# REGISTRO
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            flash("El correo ya existe.", "danger")
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Cuenta creada correctamente.", "success")

        return redirect(url_for("login"))

    return render_template("auth/register.html")


# ==================================================
# LOGIN
# ==================================================

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
            "Correo o contraseña incorrectos",
            "danger"
        )

    return render_template("auth/login.html")


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


# ==================================================
# DASHBOARD
# ==================================================

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

    subjects = len(grades)

    active_goals = len(goals)

    average = 0

    if grades:
        average = round(
            sum(g.score for g in grades)
            / len(grades),
            2
        )

    return render_template(
        "dashboard/dashboard.html",
        tasks=tasks,
        grades=grades,
        goals=goals,
        pending_tasks=pending_tasks,
        average=average,
        active_goals=active_goals,
        subjects=subjects
    )


# ==================================================
# TASKS
# ==================================================

@app.route("/tasks")
@login_required
def tasks():

    user_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "tasks/tasks.html",
        tasks=user_tasks
    )


@app.route("/task/add", methods=["POST"])
@login_required
def add_task():

    task = Task(
        title=request.form["title"],
        description=request.form["description"],
        due_date=request.form["due_date"],
        priority=request.form["priority"],
        user_id=current_user.id
    )

    db.session.add(task)
    db.session.commit()

    return redirect(url_for("tasks"))


@app.route("/task/delete/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get_or_404(id)

    db.session.delete(task)
    db.session.commit()

    return redirect(url_for("tasks"))


@app.route("/task/complete/<int:id>")
@login_required
def complete_task(id):

    task = Task.query.get_or_404(id)

    task.completed = not task.completed

    db.session.commit()

    return redirect(url_for("tasks"))


# ==================================================
# CALIFICACIONES
# ==================================================

@app.route("/grades")
@login_required
def grades():

    grades = Grade.query.filter_by(
        user_id=current_user.id
    ).all()

    average = 0

    if grades:
        average = round(
            sum(g.score for g in grades)
            / len(grades),
            2
        )

    return render_template(
        "grades/grades.html",
        grades=grades,
        average=average
    )


@app.route("/grade/add", methods=["POST"])
@login_required
def add_grade():

    grade = Grade(
        subject=request.form["subject"],
        score=float(request.form["score"]),
        user_id=current_user.id
    )

    db.session.add(grade)
    db.session.commit()

    return redirect(url_for("grades"))


@app.route("/grade/delete/<int:id>")
@login_required
def delete_grade(id):

    grade = Grade.query.get_or_404(id)

    db.session.delete(grade)

    db.session.commit()

    return redirect(url_for("grades"))


# ==================================================
# METAS
# ==================================================

@app.route("/goals")
@login_required
def goals():

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "goals/goals.html",
        goals=goals
    )


@app.route("/goal/add", methods=["POST"])
@login_required
def add_goal():

    goal = Goal(
        title=request.form["title"],
        progress=int(
            request.form["progress"]
        ),
        user_id=current_user.id
    )

    db.session.add(goal)

    db.session.commit()

    return redirect(url_for("goals"))


@app.route("/goal/update/<int:id>", methods=["POST"])
@login_required
def update_goal(id):

    goal = Goal.query.get_or_404(id)

    goal.progress = int(
        request.form["progress"]
    )

    db.session.commit()

    return redirect(url_for("goals"))


@app.route("/goal/delete/<int:id>")
@login_required
def delete_goal(id):

    goal = Goal.query.get_or_404(id)

    db.session.delete(goal)

    db.session.commit()

    return redirect(url_for("goals"))


# ==================================================
# MUSICA
# ==================================================

@app.route("/music")
@login_required
def music():
    return render_template(
        "music/music.html"
    )


# ==================================================
# PERFIL
# ==================================================

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

    return render_template(
        "profile/profile.html",
        task_count=task_count,
        grade_count=grade_count,
        goal_count=goal_count
    )


# ==================================================
# CREAR DB
# ==================================================

with app.app_context():
    db.create_all()


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
