import os
# from dotenv import load_dotenv
import asyncio
import time
import json
import discord
from discord import app_commands
from discord.utils import get
from constants_prod import Config

# load_dotenv()

class Client(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.synced = False  # Nós usamos isso para o bot não sincronizar os comandos mais de uma vez
        self.tree = app_commands.CommandTree(self)
        self.restriction_time = 10
        self.restriction_role_id = Config.Roles.ID_CARGO_RESTRICAO
        self.focus_mode_role_id = Config.Roles.ID_CARGO_LOBINHO_FOCADO
        self.gym_role_id = Config.Roles.ID_GYM_ROLE
        self.confessions_role_id = Config.Roles.ID_CONFESSIONS_ROLE
        self.cartola_role_id = Config.Roles.ID_CARTOLA_ROLE
        self.pokemon_role_id = Config.Roles.ID_POKEMON_ROLE
        self.data_file = "time_data.json"
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                data = json.load(f)
                # Converte as chaves de string para inteiros
                self.last_exit_times = {int(k): v for k, v in data.get("last_exit_times", {}).items()}
                self.removed_roles = {int(k): v for k, v in data.get("removed_roles", {}).items()}
        else:
            self.last_exit_times = {}
            self.removed_roles = {} # Dicionário para armazenar os cargos removidos por membro
            self.save_data()

    def save_data(self):
        data = {
            "last_exit_times": self.last_exit_times,
            "removed_roles": self.removed_roles #Salva os cargos removidos
        }
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)  # type: ignore

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:  # Checar se os comandos slash foram sincronizados
            await self.tree.sync(guild=discord.Object(id=Config.ID_DO_SERVIDOR))
            self.synced = True
        print(f"Entramos como {self.user}.")

        guild = self.get_guild(Config.ID_DO_SERVIDOR)
        if not guild:
            print("Servidor não encontrado. Verifique o ID.")
            return

        # Forçar a busca dos membros para preencher o cache
        print("Buscando membros do servidor para preencher o cache...")
        async for member in guild.fetch_members(limit=None):
            pass # Apenas percorre os membros para garantir que o cache seja preenchido
        print(f"Cache de membros preenchido. Total de membros: {len(guild.members)}")

        restriction_role = guild.get_role(self.restriction_role_id)
        if not restriction_role:
            print("Cargo de restrição não encontrado. Verifique o ID.")
            return

        # Para cada usuário no last_exit_times, verifica o tempo restante
        # todos os member dentro de onready renomeado para usuario
        current_time = time.time()
        for member_id, exit_time in list(self.last_exit_times.items()):
            time_since_exit = current_time - exit_time
            usuario = guild.get_member(member_id)
            if not usuario:
                print(f"Usuário {member_id} não encontrado no servidor. Removendo do last_exit_times.")
                del self.last_exit_times[member_id]
                self.save_data()
                continue

            if time_since_exit < self.restriction_time:
                # O usuário ainda está no período de restrição
                if restriction_role not in usuario.roles:
                    print(f"Adicionando cargo de restrição a {usuario} (tempo restante: {self.restriction_time - time_since_exit} segundos).")
                    await usuario.add_roles(restriction_role)

                # Agenda a remoção do cargo para o tempo restante
                remaining_time = self.restriction_time - time_since_exit
                # asyncio.create_task(self.remove_restriction(usuario, restriction_role, remaining_time))
            else:
                # O período de restrição já passou, apenas remove o registro
                print(f"Período de restrição expirado para {usuario}. Removendo do last_exit_times.")
                del self.last_exit_times[member_id]
                self.save_data()

    # async def remove_restriction(self, member, role, delay):
    #     await asyncio.sleep(delay)
    #     try:
    #         # Atualiza o objeto member para garantir que temos o estado mais recente
    #         guild = member.guild
    #         user_name = guild.get_member(member.id) # renomeei member para username
    #         if not member:
    #             print(f"Membro {member.id} não encontrado no servidor ao tentar remover o cargo de restrição.")
    #             if member.id in self.last_exit_times:
    #                 del self.last_exit_times[member.id]
    #             self.save_data()
    #             return
    #
    #         if role in member.roles:
    #             print(f"Removendo cargo {role.name} de {member} após {delay} segundos.")
    #             await member.remove_roles(role)
    #         if member.id in self.last_exit_times:
    #             print(f"Removendo {member.id} de last_exit_times.")
    #             del self.last_exit_times[member.id]
    #         self.save_data()
    #     except Exception as e:
    #         print(f"Erro ao remover o cargo de restrição: {e}")

    # MODO FOCO
    async def on_voice_state_update(self, member, before, after):
        FOCUS_CHANNEL_NAME = Config.Channels.ID_CANAL_VOZ_FOCO
        guild = self.get_guild(Config.ID_DO_SERVIDOR)
        FOCUS_LOG_CHANNEL = self.get_channel(Config.Channels.ID_CANAL_LOG_FOCO)

        restriction_time = 10
        restriction_role = member.guild.get_role(self.restriction_role_id)
        focus_mode_role = member.guild.get_role(self.focus_mode_role_id)

        gym_role = member.guild.get_role(self.gym_role_id)
        confessions_role = member.guild.get_role(self.confessions_role_id)
        cartola_role = member.guild.get_role(self.cartola_role_id)
        pokemon_role = member.guild.get_role(self.pokemon_role_id)

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

                # Lista para armazenar os cargos removidos deste membro
                removed_roles = []

                if gym_role and gym_role in member.roles:
                    await member.remove_roles(gym_role)
                    removed_roles.append(Config.Roles.ID_GYM_ROLE)

                if confessions_role and confessions_role in member.roles:
                    await member.remove_roles(confessions_role)
                    removed_roles.append(Config.Roles.ID_CONFESSIONS_ROLE)

                if cartola_role and cartola_role in member.roles:
                    await member.remove_roles(cartola_role)
                    removed_roles.append(Config.Roles.ID_CARTOLA_ROLE)

                if pokemon_role and pokemon_role in member.roles:
                    await member.remove_roles(pokemon_role)
                    removed_roles.append(Config.Roles.ID_POKEMON_ROLE)
                # teste = guild.get_member(member.id) -> cria instância de usuário "xandeub". Não atribui ID pra variável.
                # print(f'Print da variável TESTE: {teste}, tipo: {type(teste)}') -> transforma member.id em um objeto discord.member.Member (xandeub)

                # Armazena os cargos removidos no dicionário
                if removed_roles:
                    print(f"Salvando cargos removidos para {member}: {removed_roles}")
                    self.removed_roles[member.id] = removed_roles
                    self.save_data()
        # print(type(member.id)) -> int
        # print(member.id) -> printa o ID direto

        # SE O MEMBRO SAI DO CANAL DE VOZ
        if before.channel is not None and after.channel is None and before.channel.id == FOCUS_CHANNEL_NAME:

            # Registra o tempo de saída
            self.last_exit_times[member.id] = time.time()
            self.save_data()

            # Adiciona o cargo de restrição ao usuário
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

            # Remove cargo de FOCO
            await member.remove_roles(focus_mode_role)
            user = guild.get_member(member.id)
            print(f"Após guild.get_member: user = {user}")
            # member = guild.get_member(member.id) # Tira essa linha para o bot remover o cargo de restrição automaticamente
            # print(member)
            print(f"Verificando cargos removidos para member.id {member.id}. Estado atual de self.removed_roles: {self.removed_roles}")

            # Restaura os cargos que foram removidos do membro
            if user and user.id in self.removed_roles:
                print(f"Entrou no if: user.id {user.id} encontrado em self.removed_roles")
                list_of_removed_role_ids = self.removed_roles[user.id]
                print(f"Lista de cargos a restaurar: {list_of_removed_role_ids}")
                # Lista de IDs dos cargos que foram removidos
                for each_role_id in list_of_removed_role_ids:
                    role_object = guild.get_role(each_role_id)  # Obtém o objeto do cargo a partir do ID
                    if not role_object:
                        print(f"Cargo com ID {each_role_id} não encontrado no servidor.")
                        continue
                    if role_object in user.roles:
                        print(f"Membro {user} já possui o cargo {role_object.name}.")
                        continue
                    print(f"Restaurando cargo {role_object.name} para {member}.")
                    await user.add_roles(role_object)  # Adiciona o cargo de volta ao membro
                # Remove a entrada do membro do dicionário de cargos removidos
                del self.removed_roles[user.id]
                self.save_data()  # Salva as alterações no arquivo JSON
            else:
                if not user:
                    print(f"Não entrou no if: user é None (membro {member.id} não encontrado no servidor)")
                else:
                    print(f"Não entrou no if: user.id {user.id} não encontrado em self.removed_roles")

            # Pausa por 10 segundos
            await asyncio.sleep(restriction_time)

            # Remove cargo de restrição
            if restriction_role:
                await user.remove_roles(restriction_role)

            # Remove ID do membro do dicionário e deixa zerado
            if user.id in self.last_exit_times:
                del self.last_exit_times[user.id]
            self.save_data()

tribunaldo = Client()
# tribunaldo.run(Config.TOKEN) -> descomenta e apaga a parte abaixo pra rodar local

# Função que o server.py chama para rodar o bot no deploy
def run_bot():
    tribunaldo.run(Config.TOKEN)

if __name__ == "__main__":
    run_bot()

# # DESPERTAR
# @tree.command(guild=discord.Object(id=ID_DO_SERVIDOR), name='despertar', description='teste')
# async def despertar(interaction: discord.Interaction):
#     await interaction.response.send_message("Estou funcionando! AUUUUU", ephemeral=False)
#
#
# # EMBED - CARGOS DE HORAS
# @tree.command(guild=discord.Object(id=ID_DO_SERVIDOR),
#               name='embed',
#               description='Exibe os cargos de horas do servidor.')
# async def embed(interaction: discord.Interaction):
#     embed_cargos = discord.Embed(
#         title='Cargos e Quantidade de Horas do Tribunas',
#         description='''Para conseguir os cargos abaixo, basta você entrar em um canal de voz e ficar lá pela quantidade de horas necessárias para cada cargo.
#
#         As horas são cumulativas, ou seja, se você sair do canal quando tiver 1 hora, quando entrar novamete as horas continuarão a ser contadas de onde parou.''',
#         colour=9055202
#     )
#     embed_cargos.set_author(
#         name="",
#         icon_url="https://i.postimg.cc/XJq8hkd0/Design-sem-nome-1.png",
#     )
#     embed_cargos.set_thumbnail(url="https://i.postimg.cc/XJq8hkd0/Design-sem-nome-1.png")
#
#     embed_cargos.set_image(
#         url="https://i.postimg.cc/BnCdHs07/Leonardo-Phoenix-10-A-cute-cartoon-style-gray-wolf-that-is-wea-3-1.jpg")
#
#     embed_cargos.set_footer(text="Espero você nos canais de voz!")
#
#     embed_cargos.add_field(name="lobinho recruta", value="24h", inline=True)
#
#     await interaction.response.send_message(embed=embed_cargos)

# ENVIAR MENSAGENS NA DM OU CANAL
# @tree.command(guild = discord.Object(id=ID_DO_SERVIDOR), name="dm", description="Envia uma dm pra um usuário")
# @app_commands.describe(user="O usuário que vai receber a mensagem", message="A mensagem a ser enviada")
# async def dm(interaction: discord.Interaction, user: discord.User, message: str):
#     try:
#         await user.send(message)
#         await interaction.response.send_message(f"Mensagem enviada para {user.name}", ephemeral=True)
#     except discord.Forbidden:
#         await interaction.response.send_message("Não posso enviar a mensagem. DMs bloqueadas?", ephemeral=True)
#     except Exception as e:
#         await interaction.response.send_message(f"Ocorreu um erro: {e}", ephemeral=True)

'''
talvez o problema seja na ordem dos cargos:
- cargo de foco ta sendo removido DEPOIS que o de restrição é adicionado
- a verificação do member.id é feita só depois do cargo de foco ser removido... 
- talvez por isso member.id nesse momento seja None
- podemos fazer inversões e ver se dá certo
- Vai no portal developer e habilita a intent GUILD_MEMBERS
'''