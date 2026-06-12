from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'studybeat_secret_key_2026'
# La base de datos se creará en la raíz del proyecto
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studybeat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELOS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Calificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    materia = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Meta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Asegurar creación de tablas al arrancar la app
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- RUTAS ---
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        new_user = User(nombre=request.form['nombre'], correo=request.form['correo'], password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(correo=request.form['correo']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    cals = Calificacion.query.filter_by(user_id=current_user.id).all()
    promedio = sum([c.valor for c in cals]) / len(cals) if cals else 0
    return render_template('dashboard.html', promedio=round(promedio, 2))

@app.route('/tareas', methods=['GET', 'POST'])
@login_required
def tareas():
    if request.method == 'POST':
        db.session.add(Tarea(titulo=request.form['titulo'], user_id=current_user.id))
        db.session.commit()
    return render_template('tareas.html', tareas=Tarea.query.filter_by(user_id=current_user.id).all())

@app.route('/calificaciones', methods=['GET', 'POST'])
@login_required
def calificaciones():
    if request.method == 'POST':
        db.session.add(Calificacion(materia=request.form['materia'], valor=float(request.form['valor']), user_id=current_user.id))
        db.session.commit()
    return render_template('calificaciones.html', calif=Calificacion.query.filter_by(user_id=current_user.id).all())

@app.route('/metas', methods=['GET', 'POST'])
@login_required
def metas():
    if request.method == 'POST':
        db.session.add(Meta(titulo=request.form['titulo'], user_id=current_user.id))
        db.session.commit()
    return render_template('metas.html', metas=Meta.query.filter_by(user_id=current_user.id).all())

@app.route('/musica')
@login_required
def musica():
    return render_template('musica.html')

if __name__ == '__main__':
    app.run(debug=True)
