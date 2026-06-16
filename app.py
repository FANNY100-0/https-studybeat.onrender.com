from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

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

# --- Rutas CRUD ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Tareas
@app.route('/tareas', methods=['GET', 'POST'])
@login_required
def tareas():
    if request.method == 'POST':
        t = Tarea(titulo=request.form['titulo'], user_id=current_user.id)
        db.session.add(t)
        db.session.commit()
    lista = Tarea.query.filter_by(user_id=current_user.id).all()
    return render_template('tareas.html', tareas=lista)

@app.route('/tarea/delete/<int:id>')
@login_required
def delete_tarea(id):
    t = Tarea.query.get_or_404(id)
    if t.user_id == current_user.id:
        db.session.delete(t)
        db.session.commit()
    return redirect(url_for('tareas'))

# Calificaciones
@app.route('/calificaciones', methods=['GET', 'POST'])
@login_required
def calificaciones():
    if request.method == 'POST':
        c = Calificacion(materia=request.form['materia'], nota=float(request.form['nota']), user_id=current_user.id)
        db.session.add(c)
        db.session.commit()
    lista = Calificacion.query.filter_by(user_id=current_user.id).all()
    return render_template('calificaciones.html', notas=lista)

# Metas
@app.route('/metas', methods=['GET', 'POST'])
@login_required
def metas():
    if request.method == 'POST':
        m = Meta(descripcion=request.form['desc'], progreso=int(request.form['progreso']), user_id=current_user.id)
        db.session.add(m)
        db.session.commit()
    lista = Meta.query.filter_by(user_id=current_user.id).all()
    return render_template('metas.html', metas=lista)

@app.route('/musica')
@login_required
def musica():
    return render_template('musica.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
