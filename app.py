from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import os

# =========================
# APP CONFIG
# =========================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "studybeat_secret")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(base_dir, "studybeat.db")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# =========================
# LOGIN
# =========================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# =========================
# MODELOS
# =========================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.String(50))
    priority = db.Column(db.String(50))
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(150), nullable=False)
    score = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    progress = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

with app.app_context():
    db.create_all()

# =========================
# USER LOADER
# =========================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =========================
# HOME
# =========================

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

# =========================
# AUTH
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if User.query.filter_by(email=request.form["email"]).first():
            flash("El correo ya existe", "danger")
            return redirect(url_for("register"))

        hashed = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

        user = User(
            username=request.form["username"],
            email=request.form["email"],
            password=hashed
        )

        db.session.add(user)
        db.session.commit()

        flash("Cuenta creada", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        user = User.query.filter_by(email=request.form["email"]).first()

        if user and bcrypt.check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Credenciales incorrectas", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
@login_required
def dashboard():

    tasks = Task.query.filter_by(user_id=current_user.id).all()
    grades = Grade.query.filter_by(user_id=current_user.id).all()
    goals = Goal.query.filter_by(user_id=current_user.id).all()

    pending = len([t for t in tasks if not t.completed])
    completed = len([t for t in tasks if t.completed])

    average = round(sum(g.score for g in grades) / len(grades), 2) if grades else 0
    productivity = round((completed / len(tasks)) * 100, 1) if tasks else 0

    return render_template(
        "dashboard.html",
        tasks=tasks,
        grades=grades,
        goals=goals,
        pending_tasks=pending,
        completed_tasks=completed,
        average=average,
        productivity=productivity
    )

# =========================
# TASKS
# =========================

@app.route("/tasks")
@login_required
def tasks():
    data = Task.query.filter_by(user_id=current_user.id).order_by(Task.id.desc()).all()
    return render_template("tareas.html", tasks=data)


@app.route("/task/add", methods=["POST"])
@login_required
def add_task():

    if not request.form["title"]:
        flash("Título obligatorio", "danger")
        return redirect(url_for("tasks"))

    task = Task(
        title=request.form["title"],
        description=request.form.get("description"),
        due_date=request.form.get("due_date"),
        priority=request.form.get("priority"),
        user_id=current_user.id
    )

    db.session.add(task)
    db.session.commit()

    return redirect(url_for("tasks"))


@app.route("/task/delete/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()

    return redirect(url_for("tasks"))


@app.route("/task/complete/<int:id>")
@login_required
def complete_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id == current_user.id:
        task.completed = not task.completed
        db.session.commit()

    return redirect(url_for("tasks"))

# =========================
# GRADES
# =========================

@app.route("/grades")
@login_required
def grades():
    data = Grade.query.filter_by(user_id=current_user.id).all()
    return render_template("calificacion.html", grades=data)


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

# =========================
# GOALS
# =========================

@app.route("/goals")
@login_required
def goals():
    data = Goal.query.filter_by(user_id=current_user.id).all()
    return render_template("metas.html", goals=data)


@app.route("/goal/add", methods=["POST"])
@login_required
def add_goal():

    goal = Goal(
        title=request.form["title"],
        progress=int(request.form.get("progress", 0)),
        user_id=current_user.id
    )

    db.session.add(goal)
    db.session.commit()

    return redirect(url_for("goals"))

# =========================
# API STATS
# =========================

@app.route("/api/stats")
@login_required
def api_stats():

    tasks = Task.query.filter_by(user_id=current_user.id).all()
    grades = Grade.query.filter_by(user_id=current_user.id).all()
    goals = Goal.query.filter_by(user_id=current_user.id).all()

    pending = len([t for t in tasks if not t.completed])
    completed = len([t for t in tasks if t.completed])

    average = round(sum(g.score for g in grades) / len(grades), 2) if grades else 0
    productivity = round((completed / len(tasks)) * 100, 1) if tasks else 0

    return jsonify({
        "pending_tasks": pending,
        "completed_tasks": completed,
        "average": average,
        "goals": len(goals),
        "productivity": productivity
    })
