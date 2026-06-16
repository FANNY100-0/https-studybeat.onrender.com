"""
StudyBeat Enterprise Edition - Arquitectura de Software v1.0
Framework: Flask (Backend), SQLAlchemy (ORM), Flask-Login (Auth)
Descripción: Aplicación completa para gestión académica con soporte para despliegue en Render.
"""

from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os
import logging
from datetime import datetime

# --- Configuración del Sistema ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'studybeat-pro-production-2026-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studybeat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Inicialización de Módulos ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- Registro de Logs (Para diagnóstico en Render) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# --- Modelos de Base de Datos (Estructura Relacional) ---
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # Relaciones para integridad referencial
    tareas = db.relationship('Tarea', backref='author', lazy=True, cascade="all, delete-orphan")
    calificaciones = db.relationship('Calificacion', backref='author', lazy=True, cascade="all, delete-orphan")

class Tarea(db.Model):
    __tablename__ = 'tarea'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    completada = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Calificacion(db.Model):
    __tablename__ = 'calificacion'
    id = db.Column(db.Integer, primary_key=True)
    materia = db.Column(db.String(50), nullable=False)
    nota = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Meta(db.Model):
    __tablename__ = 'meta'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    progreso = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Manejadores de Errores (Robustez ante 404/500) ---
@app.errorhandler(404)
def error_404(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def error_500(e):
    return render_template('500.html'), 500

# --- Rutas del Sistema ---
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and bcrypt.check_password_hash(user.password, request.form.get('password')):
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        flash('Credenciales incorrectas.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        pw_hash = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        new_user = User(username=request.form.get('username'), email=request.form.get('email'), password=pw_hash)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    t_list = Tarea.query.filter_by(user_id=current_user.id).all()
    c_list = Calificacion.query.filter_by(user_id=current_user.id).all()
    m_list = Meta.query.filter_by(user_id=current_user.id).all()
    promedio = sum([c.nota for c in c_list]) / len(c_list) if c_list else 0
    return render_template('dashboard.html', tareas=t_list, metas=m_list, promedio=round(promedio, 2))

@app.route('/tareas', methods=['GET', 'POST', 'DELETE'])
@login_required
def tareas():
    if request.method == 'POST':
        t = Tarea(titulo=request.form.get('titulo'), user_id=current_user.id)
        db.session.add(t)
        db.session.commit()
    return render_template('tareas.html', tareas=Tarea.query.filter_by(user_id=current_user.id).all())

@app.route('/calificaciones', methods=['GET', 'POST'])
@login_required
def calificaciones():
    if request.method == 'POST':
        c = Calificacion(materia=request.form.get('materia'), nota=float(request.form.get('nota')), user_id=current_user.id)
        db.session.add(c)
        db.session.commit()
    return render_template('calificaciones.html', notas=Calificacion.query.filter_by(user_id=current_user.id).all())

@app.route('/metas', methods=['GET', 'POST'])
@login_required
def metas():
    if request.method == 'POST':
        m = Meta(descripcion=request.form.get('desc'), progreso=int(request.form.get('progreso')), user_id=current_user.id)
        db.session.add(m)
        db.session.commit()
    return render_template('metas.html', metas=Meta.query.filter_by(user_id=current_user.id).all())

@app.route('/musica')
@login_required
def musica():
    return render_template('musica.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Inicialización de Entorno ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Genera la base de datos automáticamente
    app.run(debug=True, host='0.0.0.0', port=5000)
