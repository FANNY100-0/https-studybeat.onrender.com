"""
StudyBeat - app.py
Corregido para compatibilidad con:
- Python 3.12
- Flask + Flask-SQLAlchemy 3.x (SQLAlchemy 2.x)
- Flask-Login
- Flask-Bcrypt
- Gunicorn
- Render (filesystem efímero, variables de entorno)
"""

import os
import logging

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# ---------------------------------------------------------------------------
# Configuración de logging (visible en los logs de Render)
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inicialización de la aplicación
# ---------------------------------------------------------------------------
app = Flask(__name__)

# SECRET_KEY desde variable de entorno; fallback sólo para desarrollo local
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "studybeat_dev_fallback_key_change_in_prod")

# ---------------------------------------------------------------------------
# Base de datos
# FIX #2: Render tiene filesystem efímero → usar /tmp para SQLite.
# Si existe DATABASE_URL en el entorno (PostgreSQL en Render paid tier) se usa
# automáticamente. Para SQLite local o en /tmp se construye la URI manualmente.
# ---------------------------------------------------------------------------
_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    # Render provee "postgres://..." pero SQLAlchemy 2.x requiere "postgresql://"
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = _database_url
else:
    # SQLite en /tmp — persiste mientras el proceso esté vivo en Render Free
    _db_path = os.environ.get("SQLITE_PATH", "/tmp/studybeat.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{_db_path}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,          # Detecta conexiones muertas antes de usarlas
    "pool_recycle": 300,            # Recicla conexiones cada 5 min
}

# ---------------------------------------------------------------------------
# Extensiones
# ---------------------------------------------------------------------------
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Inicia sesión para continuar."
login_manager.login_message_category = "warning"


# ---------------------------------------------------------------------------
# MODELOS
# ---------------------------------------------------------------------------
class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)

    tareas = db.relationship("Tarea", backref="owner", lazy=True, cascade="all, delete-orphan")
    calificaciones = db.relationship("Calificacion", backref="owner", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.correo}>"


class Tarea(db.Model):
    __tablename__ = "tarea"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    completada = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"<Tarea {self.titulo}>"


class Calificacion(db.Model):
    __tablename__ = "calificacion"

    id = db.Column(db.Integer, primary_key=True)
    materia = db.Column(db.String(150), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"<Calificacion {self.materia}: {self.valor}>"


# ---------------------------------------------------------------------------
# Crear tablas al arrancar (FIX #1: dentro de función, no en importación)
# ---------------------------------------------------------------------------
def create_tables():
    """Crea las tablas si no existen. Seguro para llamar múltiples veces."""
    with app.app_context():
        try:
            db.create_all()
            logger.info("Tablas de base de datos verificadas/creadas correctamente.")
        except SQLAlchemyError as e:
            logger.error(f"Error al crear tablas: {e}")
            raise


# Llamar inmediatamente al importar el módulo (compatible con Gunicorn workers)
create_tables()


# ---------------------------------------------------------------------------
# User loader para Flask-Login
# FIX #8: Usar db.session.get() en lugar de User.query.get() (deprecado en SQLAlchemy 2.x)
# ---------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, SQLAlchemyError):
        return None


# ---------------------------------------------------------------------------
# MANEJADORES DE ERRORES GLOBALES
# FIX #10 + FIX #11: Rollback en 500 para evitar sesiones corruptas
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()  # FIX #11: Limpiar sesión SQLAlchemy corrupta
    logger.error(f"Error 500: {e}")
    return render_template("500.html"), 500


@app.errorhandler(403)
def forbidden_error(e):
    return render_template("403.html"), 403


# ---------------------------------------------------------------------------
# RUTAS
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# --- LOGIN ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        # FIX #7: Validar que los campos no sean vacíos antes de consultar DB
        if not correo or not password:
            flash("Por favor completa todos los campos.", "danger")
            return render_template("login.html")

        try:
            user = User.query.filter_by(correo=correo).first()
        except SQLAlchemyError as e:
            logger.error(f"Error de DB en login: {e}")
            flash("Error interno. Intenta de nuevo.", "danger")
            return render_template("login.html")

        # FIX #7: Verificar que password no sea vacío antes de check_password_hash
        if user and password and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=False)
            next_page = request.args.get("next")
            # Validar que next_page sea una ruta relativa (evitar open redirect)
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("dashboard"))

        flash("Correo o contraseña incorrectos.", "danger")

    return render_template("login.html")


# --- REGISTRO ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        # Validaciones de campos requeridos
        if not nombre or not correo or not password:
            flash("Por favor completa todos los campos.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return render_template("register.html")

        if password_confirm and password != password_confirm:
            flash("Las contraseñas no coinciden.", "danger")
            return render_template("register.html")

        # FIX #4: Verificar correo duplicado ANTES del commit
        try:
            existing = User.query.filter_by(correo=correo).first()
        except SQLAlchemyError as e:
            logger.error(f"Error de DB al verificar duplicado: {e}")
            flash("Error interno. Intenta de nuevo.", "danger")
            return render_template("register.html")

        if existing:
            flash("Este correo ya está registrado. Inicia sesión.", "warning")
            return render_template("register.html")

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(nombre=nombre, correo=correo, password=hashed_pw)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Cuenta creada exitosamente. Inicia sesión.", "success")
            return redirect(url_for("login"))
        except IntegrityError:
            db.session.rollback()  # FIX #11
            flash("Este correo ya está registrado.", "warning")
        except SQLAlchemyError as e:
            db.session.rollback()  # FIX #11
            logger.error(f"Error al registrar usuario: {e}")
            flash("Error al crear cuenta. Intenta de nuevo.", "danger")

    return render_template("register.html")


# --- DASHBOARD ---
@app.route("/dashboard")
@login_required
def dashboard():
    try:
        total_tareas = Tarea.query.filter_by(user_id=current_user.id).count()
        tareas_pendientes = Tarea.query.filter_by(user_id=current_user.id, completada=False).count()
        calificaciones = Calificacion.query.filter_by(user_id=current_user.id).all()
        promedio = (
            round(sum(c.valor for c in calificaciones) / len(calificaciones), 2)
            if calificaciones
            else None
        )
    except SQLAlchemyError as e:
        logger.error(f"Error en dashboard: {e}")
        total_tareas = 0
        tareas_pendientes = 0
        promedio = None

    return render_template(
        "dashboard.html",
        total_tareas=total_tareas,
        tareas_pendientes=tareas_pendientes,
        promedio=promedio,
    )


# --- TAREAS ---
@app.route("/tareas", methods=["GET", "POST"])
@login_required
def tareas():
    if request.method == "POST":
        # FIX #6: Validar que titulo no sea vacío
        titulo = request.form.get("titulo", "").strip()
        if not titulo:
            flash("El título de la tarea no puede estar vacío.", "danger")
            return redirect(url_for("tareas"))

        if len(titulo) > 200:
            flash("El título es demasiado largo (máx. 200 caracteres).", "danger")
            return redirect(url_for("tareas"))

        try:
            nueva = Tarea(titulo=titulo, user_id=current_user.id)
            db.session.add(nueva)
            db.session.commit()
            flash("Tarea agregada.", "success")
        except SQLAlchemyError as e:
            db.session.rollback()  # FIX #11
            logger.error(f"Error al agregar tarea: {e}")
            flash("Error al guardar la tarea.", "danger")

        return redirect(url_for("tareas"))

    try:
        lista = Tarea.query.filter_by(user_id=current_user.id).order_by(Tarea.id.desc()).all()
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener tareas: {e}")
        lista = []
        flash("Error al cargar las tareas.", "danger")

    return render_template("tareas.html", tareas=lista)


# --- COMPLETAR TAREA ---
@app.route("/tareas/<int:tarea_id>/completar", methods=["POST"])
@login_required
def completar_tarea(tarea_id):
    try:
        tarea = db.session.get(Tarea, tarea_id)
        if not tarea or tarea.user_id != current_user.id:
            flash("Tarea no encontrada.", "warning")
            return redirect(url_for("tareas"))
        tarea.completada = not tarea.completada
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error al completar tarea: {e}")
        flash("Error al actualizar la tarea.", "danger")

    return redirect(url_for("tareas"))


# --- ELIMINAR TAREA ---
@app.route("/tareas/<int:tarea_id>/eliminar", methods=["POST"])
@login_required
def eliminar_tarea(tarea_id):
    try:
        tarea = db.session.get(Tarea, tarea_id)
        if not tarea or tarea.user_id != current_user.id:
            flash("Tarea no encontrada.", "warning")
            return redirect(url_for("tareas"))
        db.session.delete(tarea)
        db.session.commit()
        flash("Tarea eliminada.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error al eliminar tarea: {e}")
        flash("Error al eliminar la tarea.", "danger")

    return redirect(url_for("tareas"))


# --- CALIFICACIONES ---
@app.route("/calificaciones", methods=["GET", "POST"])
@login_required
def calificaciones():
    if request.method == "POST":
        materia = request.form.get("materia", "").strip()
        valor_raw = request.form.get("valor", "").strip()

        # Validar materia
        if not materia:
            flash("El nombre de la materia no puede estar vacío.", "danger")
            return redirect(url_for("calificaciones"))

        # FIX #5: Convertir valor con manejo de excepciones
        try:
            valor = float(valor_raw)
        except (ValueError, TypeError):
            flash("La calificación debe ser un número válido.", "danger")
            return redirect(url_for("calificaciones"))

        if not (0.0 <= valor <= 10.0):
            flash("La calificación debe estar entre 0 y 10.", "danger")
            return redirect(url_for("calificaciones"))

        try:
            nueva = Calificacion(materia=materia, valor=valor, user_id=current_user.id)
            db.session.add(nueva)
            db.session.commit()
            flash("Calificación registrada.", "success")
        except SQLAlchemyError as e:
            db.session.rollback()  # FIX #11
            logger.error(f"Error al guardar calificación: {e}")
            flash("Error al guardar la calificación.", "danger")

        return redirect(url_for("calificaciones"))

    try:
        lista = Calificacion.query.filter_by(user_id=current_user.id).order_by(Calificacion.materia).all()
        promedio = (
            round(sum(c.valor for c in lista) / len(lista), 2) if lista else None
        )
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener calificaciones: {e}")
        lista = []
        promedio = None
        flash("Error al cargar las calificaciones.", "danger")

    return render_template("calificaciones.html", calif=lista, promedio=promedio)


# --- ELIMINAR CALIFICACIÓN ---
@app.route("/calificaciones/<int:calif_id>/eliminar", methods=["POST"])
@login_required
def eliminar_calificacion(calif_id):
    try:
        calif = db.session.get(Calificacion, calif_id)
        if not calif or calif.user_id != current_user.id:
            flash("Calificación no encontrada.", "warning")
            return redirect(url_for("calificaciones"))
        db.session.delete(calif)
        db.session.commit()
        flash("Calificación eliminada.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error al eliminar calificación: {e}")
        flash("Error al eliminar la calificación.", "danger")

    return redirect(url_for("calificaciones"))


# --- LOGOUT ---
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Punto de entrada — desarrollo local
# FIX #9: host, port y debug explícitos
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
