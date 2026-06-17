from flask import Flask, render_template, request, redirect, url_for, jsonify, session

app = Flask(__name__)
app.secret_key = "studybeat_2026_final_key"


# =========================
# INIT DATA
# =========================
def init_data():
    if "chat" not in session:
        session["chat"] = []

    if "tasks" not in session:
        session["tasks"] = []


# =========================
# BOT BEATBOT 🎧
# =========================
def bot_response(msg):
    msg = msg.lower()

    if any(x in msg for x in ["hola", "hello", "hey"]):
        return "¡Hola! Soy BeatBot 🎧 listo para ayudarte."

    if "tarea" in msg:
        return "Ve al Planner 📚 para organizar tus tareas."

    if "musica" in msg or "música" in msg:
        return "Escucha música en la sección Music 🎶"

    if "estres" in msg or "estrés" in msg:
        return "Respira 😌, haz una pausa corta."

    if "focus" in msg:
        return "Activa Focus Mode 🔥 para concentrarte mejor."

    return "No entendí 😅 pero puedo ayudarte con estudio, tareas o música."# =========================
# HOME
# =========================
@app.route("/")
def home():
    init_data()
    return render_template("index.html")


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    init_data()
    return render_template("dashboard.html")


# =========================
# PLANNER
# =========================
@app.route("/planner", methods=["GET", "POST"])
def planner():
    init_data()

    if request.method == "POST":
        task = request.form.get("task")

        if task:
            session["tasks"].append(task)
            session.modified = True

        return redirect(url_for("planner"))

    return render_template("planner.html", tasks=session["tasks"])


# =========================
# DELETE TASK
# =========================
@app.route("/delete_task/<int:index>")
def delete_task(index):
    init_data()

    if 0 <= index < len(session["tasks"]):
        session["tasks"].pop(index)
        session.modified = True

    return redirect(url_for("planner"))


# =========================
# MUSIC
# =========================
@app.route("/music")
def music():
    return render_template("music.html")


# =========================
# FOCUS
# =========================
@app.route("/focus")
def focus():
    return render_template("focus.html")


# =========================
# SETTINGS
# =========================
@app.route("/settings")
def settings():
    return render_template("settings.html")# =========================
# BOT API
# =========================
@app.route("/bot", methods=["POST"])
def bot():
    init_data()

    data = request.get_json(force=True)
    user_msg = data.get("message", "")

    response = bot_response(user_msg)

    session["chat"].append({
        "user": user_msg,
        "bot": response
    })

    session.modified = True

    return jsonify({
        "response": response,
        "chat": session["chat"]
    })


# =========================
# GET CHAT
# =========================
@app.route("/chat")
def chat():
    init_data()
    return jsonify(session["chat"])


# =========================
# CLEAR CHAT
# =========================
@app.route("/clear_chat")
def clear_chat():
    session["chat"] = []
    session.modified = True
    return redirect(url_for("home"))


# =========================
# STATUS CHECK
# =========================
@app.route("/status")
def status():
    return jsonify({
        "app": "StudyBeat",
        "status": "running",
        "modules": {
            "bot": True,
            "planner": True,
            "music": True,
            "focus": True
        }
    })


# =========================
# ERROR HANDLER
# =========================
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "Ruta no encontrada",
        "hint": "Revisa /dashboard /planner /music /focus"
    }), 404


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
