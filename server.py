from flask import Flask
import threading
import os
from bot import run_bot  # Importa a função run_bot do bot_antigo.py

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.getenv("PORT", 10000))  # Render define a variável PORT
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Iniciar o servidor Flask em uma thread separada
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Iniciar o bot
    run_bot()