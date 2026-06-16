from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'studybeat-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studybeat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Modelos ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    completada = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Calificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    materia = db.Column(db.String(50), nullable=False)
    nota = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Meta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    progreso = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Rutas de Autenticación ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        pw = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(username=request.form['username'], email=request.form['email'], password=pw)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# --- Rutas de Dashboard y CRUD ---
@app.route('/dashboard')
@login_required
def dashboard():
    tareas = Tarea.query.filter_by(user_id=current_user.id).all()
    calificaciones = Calificacion.query.filter_by(user_id=current_user.id).all()
    metas = Meta.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', tareas=tareas, cal=calificaciones, metas=metas)

@app.route('/tarea/add', methods=['POST'])
@login_required
def add_tarea():
    nueva = Tarea(titulo=request.form['titulo'], user_id=current_user.id)
    db.session.add(nueva)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Inicialización
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
