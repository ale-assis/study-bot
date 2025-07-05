import time
import asyncio
import discord
from discord import app_commands
from constants.constants_prod import Config

# Importar os módulos
from events.focus_mode import FocusMode
from slash_commands.basic_commands import setup_commands
# from slash_commands.gemini_commands import setup_tribunaldo_chat_bot
from events.chat_bot import TribunaldoChatBot
from events.study_cam_mode import StudyCamMode

# Configuração do cliente e intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # NECESSÁRIO para ler conteúdo das mensagens
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Variáveis globais
synced = False

# Inicializar o módulo de modo foco
focus_mode = FocusMode(client)
tribunaldo_chat_bot = TribunaldoChatBot(client)
study_cam_mode = StudyCamMode(client)


@client.event
async def on_ready():
    global synced
    await client.wait_until_ready()

    if not synced:
        print("Iniciando sincronização de comandos...")
        try:
            # Configurar comandos slash
            setup_commands(tree)
            # setup_tribunaldo_chat_bot(tree, tribunaldo_chat_bot)

            # Log dos comandos registrados no CommandTree
            print(
                f"Comandos registrados no CommandTree: {[command.name for command in tree.get_commands(guild=discord.Object(id=Config.ID_DO_SERVIDOR))]}")
            await tree.sync(guild=discord.Object(id=Config.ID_DO_SERVIDOR))
            print("Comandos sincronizados com sucesso!")
            synced = True
        except Exception as e:
            print(f"Erro ao sincronizar comandos: {e}")

    print(f"Entramos como {client.user}.")

    guild = client.get_guild(Config.ID_DO_SERVIDOR)
    if not guild:
        print("Servidor não encontrado. Verifique o ID.")
        return

    # Forçar a busca dos membros para preencher o cache
    print("Buscando membros do servidor para preencher o cache...")
    async for member in guild.fetch_members(limit=None):
        pass
    print(f"Cache de membros preenchido. Total de membros: {len(guild.members)}")

    # Inicializar o modo foco e modo study cam na inicialização
    await focus_mode.initialize_restrictions()


@client.event
async def on_voice_state_update(member, before, after):
    await focus_mode.handle_voice_state_update(member, before, after)
    await study_cam_mode.handle_voice_state_update(member, before, after)


@client.event
async def on_message(message):
    """Processa mensagens para o chat bot"""
    await tribunaldo_chat_bot.handle_message(message)

def run_bot():
    """
    Função que o server.py chama para rodar o bot no deploy.
    Inclui um loop infinito com tratamento de exceções para garantir
    que o bot continue rodando mesmo após erros de conexão ou rate limit.
    """
    loop = asyncio.get_event_loop()
    while True:
        try:
            # Inicia o bot
            loop.run_until_complete(client.start(Config.TOKEN))
        except discord.errors.HTTPException as e:
            # Verifica se o erro é de "Too Many Requests" (Rate Limit)
            if e.status == 429:
                print("======================================================")
                print("Fomos bloqueados por Rate Limit (Erro 429).")
                print("Aguardando 30 minutos antes de tentar reconectar...")
                print(f"Detalhes do erro: {e.text}")
                print("======================================================")
                time.sleep(1800)  # Dorme por 30 minutos
            # Trata outros erros de HTTP
            else:
                print(f"Ocorreu um erro de HTTP não tratado: {e}")
                print("Aguardando 1 minuto antes de tentar de novo...")
                time.sleep(60)  # Espera 1 minuto
        except Exception as e:
            # Trata qualquer outro erro inesperado
            print(f"Ocorreu um erro inesperado: {e}")
            print("Aguardando 10 segundos antes de reiniciar...")
            time.sleep(10)

if __name__ == "__main__":
     run_bot()