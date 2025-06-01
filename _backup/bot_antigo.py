import discord
from discord import app_commands
from constants.constants_prod import Config
import basic_commands
from events.focus_mode import on_voice_state_update, load_data, initialize_focus_mode

# Configuração do cliente e intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

synced = False

# Carregar dados do Modo Foco
load_data()

# Eventos
@client.event
async def on_ready():
    global synced
    await client.wait_until_ready()
    if not synced:
        print("Iniciando sincronização de comandos...")
        try:
            # Log dos comandos registrados no CommandTree
            print(f"Comandos registrados no CommandTree: {[command.name for command in tree.get_commands(guild=discord.Object(id=Config.ID_DO_SERVIDOR))]}")
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

    # Inicializar o Modo Foco
    await initialize_focus_mode(guild)

# Evento on_voice_state_update
@client.event
async def on_voice_state_update(member, before, after):
    await on_voice_state_update(member, before, after)

client.run(Config.TOKEN)

# # Função que o server.py chama para rodar o bot no deploy
# def run_bot():
#     client.run(Config.TOKEN)
#
# if __name__ == "__main__":
#     run_bot()