from flask import Flask, render_template, request, redirect, url_for, jsonify, session

app = Flask(__name__)
app.secret_key = "studybeat_2026_full_app"


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
# BOT BEATBOT 🎧
# =========================
def bot_response(msg):
    msg = msg.lower()

    if any(x in msg for x in ["hola", "hello", "hey"]):
        return "¡Hola! Soy BeatBot 🎧"

    if "tarea" in msg:
        return "Ve a Tareas 📚"

    if "nota" in msg:
        return "Ve a Notas 📝"

    if "meta" in msg:
        return "Ve a Metas 🎯"

    if "estres" in msg:
        return "Respira 😌"

    return "Te ayudo con tareas, notas o metas 📚"# =========================
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

    return render_template("tareas.html", tasks=session["tasks"])


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

    return render_template("notas.html", notes=session["notes"])


# =========================
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

    return render_template("metas.html", goals=session["goals"])# =========================
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
# CHAT HISTORY
# =========================
@app.route("/chat")
def chat():
    init_data()
    return jsonify(session["chat"])


# =========================
# DELETE TASK / NOTE / GOAL
# =========================
@app.route("/delete/<tipo>/<int:index>")
def delete(tipo, index):
    init_data()

    if tipo == "tarea" and index < len(session["tasks"]):
        session["tasks"].pop(index)

    if tipo == "nota" and index < len(session["notes"]):
        session["notes"].pop(index)

    if tipo == "meta" and index < len(session["goals"]):
        session["goals"].pop(index)

    session.modified = True
    return redirect(request.referrer or url_for("home"))


# =========================
# LOGOUT / SALIR
# =========================
@app.route("/salir")
def salir():
    session.clear()
    return redirect(url_for("home"))
