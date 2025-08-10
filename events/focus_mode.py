import os
import json
import time
import asyncio
import discord
from constants.constants_prod import Config

class FocusMode:
    def __init__(self, client):
        self.client = client
        self.restriction_time = 10
        self.restriction_role_id = Config.Roles.ID_CARGO_RESTRICAO
        self.focus_mode_role_id = Config.Roles.ID_CARGO_LOBINHO_FOCADO
        self.gym_role_id = Config.Roles.ID_GYM_ROLE
        self.confessions_role_id = Config.Roles.ID_CONFESSIONS_ROLE
        self.cartola_role_id = Config.Roles.ID_CARTOLA_ROLE
        self.pokemon_role_id = Config.Roles.ID_POKEMON_ROLE
        self.gartic_role_id = Config.Roles.ID_GARTIC_ROLE
        self.xadrez_role_id = Config.Roles.ID_XADREZ_ROLE
        # Definir o caminho do arquivo usando um caminho relativo
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Diretório do script atual
        data_dir = os.path.join(base_dir, "data")  # Diretório data no mesmo nível do projeto
        os.makedirs(data_dir, exist_ok=True)  # Criar o diretório data, se não existir
        self.data_file = os.path.join(data_dir, "time_data.json")
        self.last_exit_times = {}
        self.removed_roles = {}

        # Carregar dados na inicialização
        self.load_data()

    def load_data(self):
        """Carrega os dados do arquivo JSON"""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                data = json.load(f)
                self.last_exit_times = {int(k): v for k, v in data.get("last_exit_times", {}).items()}
                self.removed_roles = {int(k): v for k, v in data.get("removed_roles", {}).items()}
        else:
            self.last_exit_times.clear()
            self.removed_roles.clear()
            self.save_data()

    def save_data(self):
        """Salva os dados no arquivo JSON"""
        data = {
            "last_exit_times": self.last_exit_times,
            "removed_roles": self.removed_roles
        }
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)

    async def initialize_restrictions(self):
        """Inicializa as restrições para usuários que saíram do canal"""
        guild = self.client.get_guild(Config.ID_DO_SERVIDOR)
        if not guild:
            print("Servidor não encontrado. Verifique o ID.")
            return

        restriction_role = guild.get_role(self.restriction_role_id)
        if not restriction_role:
            print("Cargo de restrição não encontrado. Verifique o ID.")
            return

        # Para cada usuário no last_exit_times, verifica o tempo restante
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
                if restriction_role not in usuario.roles:
                    print(
                        f"Adicionando cargo de restrição a {usuario} (tempo restante: {self.restriction_time - time_since_exit} segundos).")
                    await usuario.add_roles(restriction_role)
            else:
                print(f"Período de restrição expirado para {usuario}. Removendo do last_exit_times.")
                del self.last_exit_times[member_id]
                self.save_data()

    async def handle_voice_state_update(self, member, before, after):
        """Gerencia as mudanças de estado de voz dos membros"""
        FOCUS_CHANNEL_NAME = Config.Channels.ID_CANAL_VOZ_FOCO
        guild = self.client.get_guild(Config.ID_DO_SERVIDOR)
        FOCUS_LOG_CHANNEL = self.client.get_channel(Config.Channels.ID_CANAL_LOG_FOCO)

        # Verifica se o membro entrou no canal de foco
        if self._entered_focus_channel(before, after, FOCUS_CHANNEL_NAME):
            await self._handle_focus_enter(member, after, FOCUS_LOG_CHANNEL, guild)

        # Verifica se o membro saiu do canal de foco
        elif self._left_focus_channel(before, after, FOCUS_CHANNEL_NAME):
            await self._handle_focus_exit(member, before, FOCUS_LOG_CHANNEL, guild)

    def _entered_focus_channel(self, before, after, focus_channel_id):
        """Verifica se o membro entrou no canal de foco"""
        return ((before.channel is None and after.channel is not None and after.channel.id == focus_channel_id) or
                (before.channel is not None and before.channel.id != focus_channel_id and
                 after.channel is not None and after.channel.id == focus_channel_id))

    def _left_focus_channel(self, before, after, focus_channel_id):
        """Verifica se o membro saiu do canal de foco"""
        return (before.channel is not None and before.channel.id == focus_channel_id and
                (after.channel is None or (after.channel is not None and after.channel.id != focus_channel_id)))

    async def _handle_focus_enter(self, member, after, log_channel, guild):
        """Gerencia a entrada no canal de foco"""
        print(f"{member} entrou no canal de voz {after.channel.name}")

        # Criar embed de entrada
        embed_focus_log = discord.Embed(
            description=f"""Agora acabou a brincadeira, {member.mention}! Vai estudar que seu FUTURO DEPENDE DISSO!!! 

                    Você acabou de entrar no canal de voz {after.channel.mention} e o Modo Foco está ATIVADO! 🟢 

                    Todas as categorias e canais de texto do servidor foram OCULTADOS para evitar distrações. 
                    """,
            color=9055202
        )
        embed_focus_log.set_author(
            name="Modo Foco ATIVADO!",
            icon_url=member.avatar.url if member.avatar else None)
        embed_focus_log.set_image(
            url="https://i.postimg.cc/3JZsg5Xk/Leonardo-Phoenix-10-A-cute-gray-wolf-in-cartoon-style-is-with-2.jpg")
        embed_focus_log.add_field(
            name="👍 Para visualizá-los novamente, basta SAIR do canal [https://discord.com/channels/1013854219058544720/1359594696061485126] e esperar alguns segundos que todos os canais ocultos reaparecerão magicamente!",
            value="Bons estudos! 💪")
        embed_focus_log.add_field(
            name="⚠️ ATENÇÃO: Se você saiu do canal [https://discord.com/channels/1013854219058544720/1359594696061485126] e os canais do servidor não apareceram para você, não se preocupe! Basta seguir o passo a passo aqui 👇:",
            value="https://discord.com/channels/1013854219058544720/1359594696061485126/1377073863053279273",
            inline=False)

        await log_channel.send(member.mention, embed=embed_focus_log)

        # Adicionar cargo de modo foco e remover outros cargos
        focus_mode_role = guild.get_role(self.focus_mode_role_id)
        if focus_mode_role and focus_mode_role not in member.roles:
            await member.add_roles(focus_mode_role)
            await self._remove_distraction_roles(member, guild)

    async def _remove_distraction_roles(self, member, guild):
        """Remove cargos que podem causar distração durante o modo foco"""
        gym_role = guild.get_role(self.gym_role_id)
        confessions_role = guild.get_role(self.confessions_role_id)
        cartola_role = guild.get_role(self.cartola_role_id)
        pokemon_role = guild.get_role(self.pokemon_role_id)
        gartic_role = guild.get_role(self.gartic_role_id)
        xadrez_role = guild.get_role(self.xadrez_role_id)

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

        if gartic_role and gartic_role in member.roles:
            await member.remove_roles(gartic_role)
            removed_roles_list.append(Config.Roles.ID_GARTIC_ROLE)

        if xadrez_role and xadrez_role in member.roles:
            await member.remove_roles(xadrez_role)
            removed_roles_list.append(Config.Roles.ID_XADREZ_ROLE)

        if removed_roles_list:
            print(f"Salvando cargos removidos para {member}: {removed_roles_list}")
            self.removed_roles[member.id] = removed_roles_list
            self.save_data()

    async def _handle_focus_exit(self, member, before, log_channel, guild):
        """Gerencia a saída do canal de foco"""
        self.last_exit_times[member.id] = time.time()
        self.save_data()

        # Adicionar cargo de restrição
        restriction_role = guild.get_role(self.restriction_role_id)
        if restriction_role:
            await member.add_roles(restriction_role)

        print(f"{member} saiu do canal de voz {before.channel.name}")

        # Criar embed de saída
        embed_focus_log = discord.Embed(
            description=f"""AUUUUUUU! Estou orgulhoso de você, {member.mention}! Parabéns pelo foco hoje, você está um pouco mais perto de realizar seu SONHO!  

                    Agora que você saiu do canal no canal de voz {before.channel.mention}, o Modo Foco está DESATIVADO! 🔴 
                    """,
            color=9055202
        )
        embed_focus_log.set_author(
            name="Modo Foco DESATIVADO!",
            icon_url=member.avatar.url if member.avatar else None)
        embed_focus_log.set_image(
            url="https://i.postimg.cc/4NCcpjfR/Leonardo-Phoenix-10-A-cute-gray-wolf-in-cartoon-style-is-with-1.jpg")
        embed_focus_log.add_field(
            name="✨ Todas as categorias e canais de texto do servidor estão voltando a aparecer aos pouquinhos e magicamente!",
            value="É só aguardar cerca de 2 segundos e você conseguirá visualizar todos os canais novamente.")
        embed_focus_log.add_field(
            name="⚠️ ATENÇÃO: Se você saiu do canal [https://discord.com/channels/1013854219058544720/1359594696061485126] e os canais do servidor não apareceram para você, não se preocupe! Basta seguir o passo a passo aqui 👇:",
            value="https://discord.com/channels/1013854219058544720/1359594696061485126/1377073863053279273",
            inline=False)

        await log_channel.send(member.mention, embed=embed_focus_log)

        # Remover cargo de modo foco e restaurar cargos removidos
        focus_mode_role = guild.get_role(self.focus_mode_role_id)
        await member.remove_roles(focus_mode_role)

        user = guild.get_member(member.id)
        await self._restore_removed_roles(user, guild)

        # Aguardar tempo de restrição e depois remover a restrição
        await asyncio.sleep(self.restriction_time)

        if restriction_role and user:
            await user.remove_roles(restriction_role)

        if user and user.id in self.last_exit_times:
            del self.last_exit_times[user.id]
        self.save_data()

    async def _restore_removed_roles(self, user, guild):
        """Restaura os cargos que foram removidos durante o modo foco"""
        print(f"Após guild.get_member: user = {user}")
        print(
            f"Verificando cargos removidos para member.id {user.id if user else 'None'}. Estado atual de removed_roles: {self.removed_roles}")

        if user and user.id in self.removed_roles:
            print(f"Entrou no if: user.id {user.id} encontrado em removed_roles")
            list_of_removed_role_ids = self.removed_roles[user.id]
            print(f"Lista de cargos a restaurar: {list_of_removed_role_ids}")

            for each_role_id in list_of_removed_role_ids:
                role_object = guild.get_role(each_role_id)
                if not role_object:
                    print(f"Cargo com ID {each_role_id} não encontrado no servidor.")
                    continue
                if role_object in user.roles:
                    print(f"Membro {user} já possui o cargo {role_object.name}.")
                    continue
                print(f"Restaurando cargo {role_object.name} para {user}.")
                await user.add_roles(role_object)

            del self.removed_roles[user.id]
            self.save_data()
        else:
            if not user:
                print(f"Não entrou no if: user é None (membro não encontrado no servidor)")
            else:
                print(f"Não entrou no if: user.id {user.id} não encontrado em removed_roles")