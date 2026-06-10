from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

# =========================
# CONFIGURACIÓN
# =========================

app = Flask(__name__)

app.config["SECRET_KEY"] = "studybeat_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Inicia sesión para continuar."


# =========================
# MODELOS
# =========================

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    tareas = db.relationship("Tarea", backref="usuario", lazy=True)
    calificaciones = db.relationship("Calificacion", backref="usuario", lazy=True)
    metas = db.relationship("Meta", backref="usuario", lazy=True)


class Tarea(db.Model):
    __tablename__ = "tareas"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_limite = db.Column(db.String(50))
    prioridad = db.Column(db.String(20))
    completada = db.Column(db.Boolean, default=False)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )


class Calificacion(db.Model):
    __tablename__ = "calificaciones"

    id = db.Column(db.Integer, primary_key=True)
    materia = db.Column(db.String(100), nullable=False)
    calificacion = db.Column(db.Float, nullable=False)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )


class Meta(db.Model):
    __tablename__ = "metas"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    progreso = db.Column(db.Integer, default=0)
    fecha_objetivo = db.Column(db.String(50))

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )


# =========================
# FLASK LOGIN
# =========================

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# =========================
# INICIO
# =========================

@app.route("/")
def index():
    return render_template("index.html")


# =========================
# REGISTRO
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        password = request.form.get("password")

        usuario_existente = Usuario.query.filter_by(
            correo=correo
        ).first()

        if usuario_existente:
            flash("El correo ya está registrado.", "danger")
            return redirect(url_for("register"))

        password_hash = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            password=password_hash
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Registro exitoso.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        correo = request.form.get("correo")
        password = request.form.get("password")

        usuario = Usuario.query.filter_by(
            correo=correo
        ).first()

        if usuario and bcrypt.check_password_hash(
            usuario.password,
            password
        ):

            login_user(usuario)

            flash(
                "Bienvenido a StudyBeat",
                "success"
            )

            return redirect(url_for("dashboard"))

        flash(
            "Correo o contraseña incorrectos",
            "danger"
        )

    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Sesión cerrada correctamente",
        "info"
    )

    return redirect(url_for("login"))


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
@login_required
def dashboard():

    tareas_pendientes = Tarea.query.filter_by(
        usuario_id=current_user.id,
        completada=False
    ).count()

    metas_activas = Meta.query.filter_by(
        usuario_id=current_user.id
    ).count()

    calificaciones = Calificacion.query.filter_by(
        usuario_id=current_user.id
    ).all()

    promedio = 0

    if calificaciones:
        promedio = round(
            sum(c.calificacion for c in calificaciones)
            / len(calificaciones),
            2
        )

    return render_template(
        "dashboard.html",
        tareas=tareas_pendientes,
        metas=metas_activas,
        promedio=promedio
    )


# =========================
# PERFIL
# =========================

@app.route("/perfil")
@login_required
def perfil():
    return render_template("perfil.html")


# =========================
# MÚSICA
# =========================

@app.route("/musica")
@login_required
def musica():
    return render_template("musica.html")


# =========================
# CREAR BASE DE DATOS
# =========================

with app.app_context():
    db.create_all()


# =========================
# EJECUCIÓN LOCAL
# =========================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
