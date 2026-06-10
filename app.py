from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    # Aquí puedes añadir más diseño usando HTML y CSS
    return """
    <html>
        <head>
            <style>
                body { background-color: #f0f2f5; font-family: Arial, sans-serif; text-align: center; }
                h1 { color: #4a90e2; }
                .container { margin-top: 50px; padding: 20px; background: white; border-radius: 10px; display: inline-block; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎵 StudyBeat</h1>
                <p>Bienvenida a tu espacio de concentración.</p>
                <button onclick="alert('¡Funcionalidad en camino!')">Empezar a estudiar</button>
            </div>
        </body>
    </html>
    """

if __name__ == '__main__':
    app.run()
if __name__ == '__main__':
    app.run()
