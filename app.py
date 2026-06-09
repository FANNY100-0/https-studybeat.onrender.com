from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>🎵 StudyBeat</h1>
    <p>¡Tu plataforma está funcionando!</p>
    """
