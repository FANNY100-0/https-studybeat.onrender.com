from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "studybeat_2026"

# =========================
# GESTIÓN DE DATOS EN SESIÓN
# =========================
def init_data():
    """Inicializa las listas en la sesión si no existen."""
    if "tasks" not in session:
        session["tasks"] = []
    if "notes" not in session:
        session["notes"] = []
    if "agenda" not in session:
        session["agenda"] = []

# =========================
# RUTAS PRINCIPALES
# =========================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/tareas", methods=["GET", "POST"])
def tareas():
    init_data()
    if request.method == "POST":
        task = request.form.get("task")
        if task:
            session["tasks"].append(task)
            session.modified = True
        return redirect(url_for("tareas"))
    return render_template("tareas.html", tasks=session["tasks"])

@app.route("/notas", methods=["GET", "POST"])
def notas():
    init_data()
    if request.method == "POST":
        note = request.form.get("note")
        if note:
            session["notes"].append(note)
            session.modified = True
        return redirect(url_for("notas"))
    return render_template("notas.html", notes=session["notes"])

@app.route("/agenda", methods=["GET", "POST"])
def agenda():
    init_data()
    if request.method == "POST":
        event = request.form.get("event")
        if event:
            session["agenda"].append(event)
            session.modified = True
        return redirect(url_for("agenda"))
    return render_template("agenda.html", agenda=session["agenda"])

# =========================
# RUTAS DE UTILIDADES Y VISTAS
# =========================

@app.route("/calendario")
def calendario():
    return render_template("calendario.html")

@app.route("/voz")
def voz():
    return render_template("voz.html")

@app.route("/musica")
def musica():
    return render_template("musica.html")

# =========================
# LÓGICA DE ELIMINACIÓN
# =========================

@app.route("/delete/<tipo>/<int:index>")
def delete(tipo, index):
    init_data()
    # Mapeo de tipos para simplificar la lógica
    mapeo = {"tarea": "tasks", "nota": "notes", "agenda": "agenda"}
    
    key = mapeo.get(tipo)
    if key and 0 <= index < len(session[key]):
        session[key].pop(index)
        session.modified = True
        
    return redirect(request.referrer or url_for("home"))

@app.route("/salir")
def salir():
    session.clear()
    return redirect(url_for("home"))

# =========================
# GESTIÓN DE ERRORES
# =========================

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

# =========================
# EJECUCIÓN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
