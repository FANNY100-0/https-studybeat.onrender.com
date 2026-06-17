from flask import Flask, render_template, request, redirect, url_for, jsonify, session

app = Flask(__name__)
app.secret_key = "studybeat_fixed_2026"


# =========================
# INIT DATA
# =========================
def init_data():
    if "chat" not in session:
        session["chat"] = []

    if "tasks" not in session:
        session["tasks"] = []

    if "notes" not in session:
        session["notes"] = []

    if "goals" not in session:
        session["goals"] = []


# =========================
# BOT LOGIC
# =========================
def bot_response(msg):
    msg = msg.lower()

    if "hola" in msg:
        return "Hola 👋 soy BeatBot"

    if "tarea" in msg:
        return "Ve a la sección de tareas 📚"

    if "nota" in msg:
        return "Ve a la sección de notas 📝"

    if "meta" in msg:
        return "Ve a la sección de metas 🎯"

    if "estres" in msg:
        return "Respira profundo 😌"

    return "Puedo ayudarte con tareas, notas y metas."# =========================
# HOME
# =========================
@app.route("/")
def home():
    init_data()
    return render_template("index.html")


# =========================
# TAREAS
# =========================
@app.route("/tareas", methods=["GET", "POST"])
def tareas():
    init_data()

    if request.method == "POST":
        task = request.form.get("task")

        if task:
            session["tasks"].append(task)
            session.modified = True

        return redirect(url_for("tareas"))

    return render_template(
        "tareas.html",
        tasks=session["tasks"]
    )


# =========================
# NOTAS
# =========================
@app.route("/notas", methods=["GET", "POST"])
def notas():
    init_data()

    if request.method == "POST":
        note = request.form.get("note")

        if note:
            session["notes"].append(note)
            session.modified = True

        return redirect(url_for("notas"))

    return render_template(
        "notas.html",
        notes=session["notes"]
    )# =========================
# METAS
# =========================
@app.route("/metas", methods=["GET", "POST"])
def metas():
    init_data()

    if request.method == "POST":
        goal = request.form.get("goal")

        if goal:
            session["goals"].append(goal)
            session.modified = True

        return redirect(url_for("metas"))

    return render_template(
        "metas.html",
        goals=session["goals"]
    )# =========================
# MUSICA
# =========================
@app.route("/musica")
def musica():
    canciones = [
        {
            "nombre": "Lofi Study",
            "url": "https://www.youtube.com/embed/jfKfPfyJRdk"
        }
    ]

    return render_template(
        "musica.html",
        canciones=canciones
    )


# =========================
# ELIMINAR
# =========================
@app.route("/delete/<tipo>/<int:index>")
def delete(tipo, index):
    init_data()

    if tipo == "tarea":
        if 0 <= index < len(session["tasks"]):
            session["tasks"].pop(index)

    elif tipo == "nota":
        if 0 <= index < len(session["notes"]):
            session["notes"].pop(index)

    elif tipo == "meta":
        if 0 <= index < len(session["goals"]):
            session["goals"].pop(index)

    session.modified = True

    return redirect(
        request.referrer or url_for("home")
    )# =========================
# BOT API
# =========================
@app.route("/bot", methods=["POST"])
def bot():
    init_data()

    data = request.get_json(force=True)

    msg = data.get("message", "")

    response = bot_response(msg)

    session["chat"].append({
        "user": msg,
        "bot": response
    })

    session.modified = True

    return jsonify({
        "response": response,
        "chat": session["chat"]
    })


# =========================
# CHAT
# =========================
@app.route("/chat")
def chat():
    init_data()

    return jsonify(session["chat"])# =========================
# SALIR
# =========================
@app.route("/salir")
def salir():
    session.clear()
    return redirect(url_for("home"))


# =========================
# STATUS
# =========================
@app.route("/status")
def status():
    return jsonify({
        "app": "StudyBeat",
        "status": "ok"
    })


# =========================
# ERROR 404
# =========================
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Ruta no encontrada"
    }), 404


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
