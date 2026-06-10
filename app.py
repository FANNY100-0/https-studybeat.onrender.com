from flask import Flask

app = Flask(__name__)

# Esta es la ruta raíz que cargará tu página
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>StudyBeat</title>
        <style>
            body { font-family: sans-serif; background: #0f172a; color: white; text-align: center; padding: 50px; }
            h1 { color: #22c55e; }
        </style>
    </head>
    <body>
        <h1>StudyBeat</h1>
        <p>¡Tu plataforma está funcionando correctamente!</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run()
