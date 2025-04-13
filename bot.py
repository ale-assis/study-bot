import os
import asyncio
import time
import json
import discord
from discord import app_commands
from discord.utils import get
from constants_prod import Config

# Configuração do cliente e intents
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Variáveis globais (equivalentes aos atributos da classe Client)
synced = False
restriction_time = 10
restriction_role_id = Config.Roles.ID_CARGO_RESTRICAO
focus_mode_role_id = Config.Roles.ID_CARGO_LOBINHO_FOCADO
gym_role_id = Config.Roles.ID_GYM_ROLE
confessions_role_id = Config.Roles.ID_CONFESSIONS_ROLE
cartola_role_id = Config.Roles.ID_CARTOLA_ROLE
pokemon_role_id = Config.Roles.ID_POKEMON_ROLE
data_file = "time_data.json"
last_exit_times = {}
removed_roles = {}

# Funções auxiliares
def load_data():
    global last_exit_times, removed_roles
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            data = json.load(f)
            last_exit_times = {int(k): v for k, v in data.get("last_exit_times", {}).items()}
            removed_roles = {int(k): v for k, v in data.get("removed_roles", {}).items()}
    else:
        last_exit_times.clear()
        removed_roles.clear()
        save_data()

def save_data():
    data = {
        "last_exit_times": last_exit_times,
        "removed_roles": removed_roles
    }
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

# Inicializar os dados
load_data()

# Slash Commands
@tree.command(name="despertar", description="verifica se o tribunaldo está acordado", guild=discord.Object(id=Config.ID_DO_SERVIDOR))
async def despertar(interaction: discord.Interaction):
    print(f"Comando /despertar chamado por {interaction.user}")
    await interaction.response.send_message("Estou funcionando! AUUUUU 🐺", ephemeral=False)

# @tree.command(name="sync", description="Sincroniza os comandos manualmente", guild=discord.Object(id=Config.ID_DO_SERVIDOR))
# async def sync(interaction: discord.Interaction):
#     print("Forçando sincronização de comandos...")
#     try:
#         await tree.sync(guild=discord.Object(id=Config.ID_DO_SERVIDOR))
#         await interaction.response.send_message("Comandos sincronizados!", ephemeral=True)
#         print("Comandos sincronizados com sucesso via /sync!")
#     except Exception as e:
#         print(f"Erro ao sincronizar comandos via /sync: {e}")
#         await interaction.response.send_message(f"Erro ao sincronizar: {e}", ephemeral=True)

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

    restriction_role = guild.get_role(restriction_role_id)
    if not restriction_role:
        print("Cargo de restrição não encontrado. Verifique o ID.")
        return

    # Para cada usuário no last_exit_times, verifica o tempo restante
    current_time = time.time()
    for member_id, exit_time in list(last_exit_times.items()):
        time_since_exit = current_time - exit_time
        usuario = guild.get_member(member_id)
        if not usuario:
            print(f"Usuário {member_id} não encontrado no servidor. Removendo do last_exit_times.")
            del last_exit_times[member_id]
            save_data()
            continue

        if time_since_exit < restriction_time:
            if restriction_role not in usuario.roles:
                print(f"Adicionando cargo de restrição a {usuario} (tempo restante: {restriction_time - time_since_exit} segundos).")
                await usuario.add_roles(restriction_role)
        else:
            print(f"Período de restrição expirado para {usuario}. Removendo do last_exit_times.")
            del last_exit_times[member_id]
            save_data()

@client.event
async def on_voice_state_update(member, before, after):
    FOCUS_CHANNEL_NAME = Config.Channels.ID_CANAL_VOZ_FOCO
    guild = client.get_guild(Config.ID_DO_SERVIDOR)
    FOCUS_LOG_CHANNEL = client.get_channel(Config.Channels.ID_CANAL_LOG_FOCO)

    restriction_role = guild.get_role(restriction_role_id)
    focus_mode_role = guild.get_role(focus_mode_role_id)

    gym_role = guild.get_role(gym_role_id)
    confessions_role = guild.get_role(confessions_role_id)
    cartola_role = guild.get_role(cartola_role_id)
    pokemon_role = guild.get_role(pokemon_role_id)

    # SE O MEMBRO ENTRA NO CANAL DE VOZ
    if before.channel is None and after.channel is not None and after.channel.id == FOCUS_CHANNEL_NAME:
        print(f"{member} entrou no canal de voz {after.channel.name}")

        embed_focus_log = discord.Embed(
            description=f"""Agora acabou a brincadeira, {member.mention}! Vai estudar que seu FUTURO DEPENDE DISSO!!! 

            Você acabou de entrar no canal de voz {after.channel.mention} e o Modo Foco está ATIVADO! 🟢 

            Todas as categorias e canais de texto do servidor foram ocultados para evitar distrações. 
            """,
            color=9055202
        )
        embed_focus_log.set_author(name="Modo Foco ATIVADO!", icon_url=member.avatar.url if member.avatar else None)
        embed_focus_log.set_image(url="https://i.postimg.cc/3JZsg5Xk/Leonardo-Phoenix-10-A-cute-gray-wolf-in-cartoon-style-is-with-2.jpg")
        embed_focus_log.add_field(name="Para visualizá-los novamente, basta SAIR do canal e esperar alguns segundos que todos os canais começarão a aparecer magicamente! 👀✨", value="Bons estudos! 💪")

        await FOCUS_LOG_CHANNEL.send(member.mention, embed=embed_focus_log)

        if focus_mode_role and focus_mode_role not in member.roles:
            await member.add_roles(focus_mode_role)

            removed_roles_list = []

            if gym_role and gym_role in member.roles:
                await member.remove_roles(gym_role)
                removed_roles_list.append(Config.Roles.ID_GYM_ROLE)

            if confessions_role and confessions_role in member.roles:
                await member.remove_roles(confessions_role)
                removed_roles_list.append(Config.Roles.ID_CONFESSIONS_ROLE)

            if cartola_role and cartola_role in member.roles:
                await member.remove_roles(cartola_role)
                removed_roles_list.append(Config.Roles.ID_CARTOLA_ROLE)

            if pokemon_role and pokemon_role in member.roles:
                await member.remove_roles(pokemon_role)
                removed_roles_list.append(Config.Roles.ID_POKEMON_ROLE)

            if removed_roles_list:
                print(f"Salvando cargos removidos para {member}: {removed_roles_list}")
                removed_roles[member.id] = removed_roles_list
                save_data()

    # SE O MEMBRO SAI DO CANAL DE VOZ
    if (before.channel is not None and before.channel.id == FOCUS_CHANNEL_NAME and
    (after.channel is None or (after.channel is not None and after.channel.id != FOCUS_CHANNEL_NAME))):
        last_exit_times[member.id] = time.time()
        save_data()

        if restriction_role:
            await member.add_roles(restriction_role)

        print(f"{member} saiu do canal de voz {before.channel.name}")
        embed_focus_log = discord.Embed(
            description=f"""AUUUUUUU! Estou orgulhoso de você, {member.mention}! Parabéns pelo foco hoje, você está um pouco mais perto de realizar seu SONHO!  

            Agora que você saiu do canal no canal de voz {before.channel.mention}, o Modo Foco está DESATIVADO! 🔴 
            """,
            color=9055202
        )
        embed_focus_log.set_author(name="Modo Foco DESATIVADO!", icon_url=member.avatar.url if member.avatar else None)
        embed_focus_log.set_image(url="https://i.postimg.cc/4NCcpjfR/Leonardo-Phoenix-10-A-cute-gray-wolf-in-cartoon-style-is-with-1.jpg")
        embed_focus_log.add_field(name="Todas as categorias e canais de texto do servidor estão voltando a aparecer aos pouquinhos e magicamente! 👀✨", value="É só aguardar cerca de 10 segundos e você conseguirá visualizar todos os canais novamente.")

        await FOCUS_LOG_CHANNEL.send(member.mention, embed=embed_focus_log)

        await member.remove_roles(focus_mode_role)
        user = guild.get_member(member.id)
        print(f"Após guild.get_member: user = {user}")
        print(f"Verificando cargos removidos para member.id {member.id}. Estado atual de removed_roles: {removed_roles}")

        if user and user.id in removed_roles:
            print(f"Entrou no if: user.id {user.id} encontrado em removed_roles")
            list_of_removed_role_ids = removed_roles[user.id]
            print(f"Lista de cargos a restaurar: {list_of_removed_role_ids}")
            for each_role_id in list_of_removed_role_ids:
                role_object = guild.get_role(each_role_id)
                if not role_object:
                    print(f"Cargo com ID {each_role_id} não encontrado no servidor.")
                    continue
                if role_object in user.roles:
                    print(f"Membro {user} já possui o cargo {role_object.name}.")
                    continue
                print(f"Restaurando cargo {role_object.name} para {member}.")
                await user.add_roles(role_object)
            del removed_roles[user.id]
            save_data()
        else:
            if not user:
                print(f"Não entrou no if: user é None (membro {member.id} não encontrado no servidor)")
            else:
                print(f"Não entrou no if: user.id {user.id} não encontrado em removed_roles")

        await asyncio.sleep(restriction_time)

        if restriction_role:
            await user.remove_roles(restriction_role)

        if user.id in last_exit_times:
            del last_exit_times[user.id]
        save_data()

# client.run(Config.TOKEN)

# Função que o server.py chama para rodar o bot no deploy
def run_bot():
    client.run(Config.TOKEN)

if __name__ == "__main__":
    run_bot()