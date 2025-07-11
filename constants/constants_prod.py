import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv("TOKEN")
    ID_DO_SERVIDOR = int(os.getenv("ID_DO_SERVIDOR"))
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    class Channels:
        ID_CANAL_VOZ_FOCO = int(os.getenv("ID_CANAL_VOZ_FOCO"))
        ID_CANAL_LOG_FOCO = int(os.getenv("ID_CANAL_LOG_FOCO"))
        ID_CANAL_CHAT_BOT = int(os.getenv("ID_CANAL_CHAT_BOT"))
        ID_CANAL_VOZ_CAMERA = int(os.getenv("ID_CANAL_VOZ_CAMERA"))

    class Roles:
        ID_CARGO_RESTRICAO = int(os.getenv("ID_CARGO_RESTRICAO"))
        ID_CARGO_LOBINHO_FOCADO = int(os.getenv("ID_CARGO_LOBINHO_FOCADO"))
        ID_GYM_ROLE = int(os.getenv("ID_GYM_ROLE"))
        ID_CONFESSIONS_ROLE = int(os.getenv("ID_CONFESSIONS_ROLE"))
        ID_CARTOLA_ROLE = int(os.getenv("ID_CARTOLA_ROLE"))
        ID_POKEMON_ROLE = int(os.getenv("ID_POKEMON_ROLE"))
        ID_GARTIC_ROLE = int(os.getenv("ID_GARTIC_ROLE"))
        ID_XADREZ_ROLE = int(os.getenv("ID_XADREZ_ROLE"))