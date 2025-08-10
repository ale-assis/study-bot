import os
import json
import time
import asyncio
import discord
from constants.constants_prod import Config


class StudyCamMode:
    def __init__(self, client):
        self.client = client
        self.warning_time = 60  # 60 segundos para ligar câmera/transmissão
        self.study_cam_channel_id = Config.Channels.ID_CANAL_VOZ_CAMERA
        self.warning_channel_id = Config.Channels.ID_CANAL_LOG_FOCO

        # Dicionário para armazenar membros que estão sendo monitorados (entrada)
        self.monitoring_members = {}

        # NOVO: Dicionário para monitoramento contínuo de membros no canal
        self.continuous_monitoring = {}

        # NOVO: Dicionário para rastrear expulsões do bot
        self.bot_kicked_members = set()

        # Arquivo para persistir dados se necessário
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.data_file = os.path.join(data_dir, "study_cam_data.json")

        self.load_data()

    def load_data(self):
        """Carrega os dados do arquivo JSON"""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                data = json.load(f)
        else:
            self.save_data()

    def save_data(self):
        """Salva os dados no arquivo JSON"""
        data = {
            "last_updated": time.time(),
            "total_warnings": getattr(self, 'total_warnings', 0),
            "total_kicks": getattr(self, 'total_kicks', 0),
            "total_compliances": getattr(self, 'total_compliances', 0)
        }
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)

    async def handle_voice_state_update(self, member, before, after):
        """Gerencia as mudanças de estado de voz dos membros no canal de estudo com câmera"""

        if self._entered_study_cam_channel(before, after):
            await self._handle_study_cam_enter(member, after)
        elif self._left_study_cam_channel(before, after):
            await self._handle_study_cam_exit(member)
        elif self._updated_in_study_cam_channel(before, after):
            await self._handle_study_cam_update(member, after)

    def _entered_study_cam_channel(self, before, after):
        """Verifica se o membro entrou no canal de estudo com câmera"""
        return ((
                        before.channel is None and after.channel is not None and after.channel.id == self.study_cam_channel_id) or
                (before.channel is not None and before.channel.id != self.study_cam_channel_id and
                 after.channel is not None and after.channel.id == self.study_cam_channel_id))

    def _left_study_cam_channel(self, before, after):
        """Verifica se o membro saiu do canal de estudo com câmera"""
        return (before.channel is not None and before.channel.id == self.study_cam_channel_id and
                (after.channel is None or (
                        after.channel is not None and after.channel.id != self.study_cam_channel_id)))

    def _updated_in_study_cam_channel(self, before, after):
        """Verifica se o membro atualizou o estado no canal de estudo com câmera"""
        return (before.channel is not None and before.channel.id == self.study_cam_channel_id and
                after.channel is not None and after.channel.id == self.study_cam_channel_id)

    def _has_camera_or_screen_share(self, voice_state):
        """Verifica se o membro tem câmera ou transmissão de tela ligada"""
        return voice_state.self_video or voice_state.self_stream

    def _format_time_remaining(self, seconds):
        """Formata o tempo restante de forma mais amigável"""
        if seconds > 30:
            return f"{seconds} segundos ⏰"
        elif seconds > 10:
            return f"{seconds} segundos ⚠️"
        else:
            return f"{seconds} segundos 🚨"

    async def _handle_study_cam_enter(self, member, after):
        """Gerencia a entrada no canal de estudo com câmera"""
        print(f"{member} entrou no canal de estudo com câmera {after.channel.name}")

        # NOVO: Remover da lista de expulsos quando entrar novamente
        if member.id in self.bot_kicked_members:
            self.bot_kicked_members.remove(member.id)

        # Se já tem câmera ou transmissão ligada, enviar mensagem de boas-vindas
        if self._has_camera_or_screen_share(after):
            warning_channel = self.client.get_channel(self.warning_channel_id)
            if warning_channel:
                embed = discord.Embed(
                    title="✅ Bem-vindo ao Canal de Estudo!",
                    description=f"""Olá {member.mention}! 

                    Você entrou no canal **{after.channel.name}** e já está com sua câmera/transmissão ligada!

                    **📚 Excelente!** Você pode continuar estudando tranquilamente.

                    Bons estudos! 📖✨""",
                    color=0x00FF00  # Verde
                )
                embed.set_thumbnail(
                    url="https://i.postimg.cc/52m91bny/Leonardo-Phoenix-10-A-cute-cartoon-style-wolf-who-is-studying-2-removebg-preview-3.png")
                embed.set_footer(text="Tribunaldo Bot | Tribunas Study")

                # Enviar mensagem que será deletada automaticamente em 30 segundos
                message = await warning_channel.send(embed=embed)
                # Agendar deleção da mensagem após 30 segundos (sem bloquear)
                asyncio.create_task(self._delete_message_after_delay(message, 30))
            return

        # Criar aviso para membros sem câmera/transmissão
        warning_channel = self.client.get_channel(self.warning_channel_id)
        if warning_channel:
            embed = discord.Embed(
                title="⚠️ Aviso - Canal de Estudo com Câmera",
                description=f"""Olá {member.mention}! 

                Você entrou no canal [https://discord.com/channels/1013854219058544720/1380897477108039740] que é destinado para estudos com câmera/transmissão de tela ligada.

                **📹 ATENÇÃO:** Você tem **{self.warning_time} segundos** para ligar sua **câmera** ou **transmissão de tela**.

                Se não ligar uma das duas opções dentro deste prazo, será automaticamente expulso do canal.""",
                color=0xFFD700  # Cor dourada para aviso
            )

            embed.add_field(
                name="⏰ Tempo restante",
                value=self._format_time_remaining(self.warning_time),
                inline=False
            )

            embed.set_thumbnail(
                url="https://i.postimg.cc/52m91bny/Leonardo-Phoenix-10-A-cute-cartoon-style-wolf-who-is-studying-2-removebg-preview-3.png")
            embed.set_footer(text="Tribunaldo Bot | Tribunas Study")

            warning_message = await warning_channel.send(member.mention, embed=embed)

            # Iniciar monitoramento com contador regressivo
            monitor_task = asyncio.create_task(self._monitor_member_with_countdown(member, warning_message))

            self.monitoring_members[member.id] = {
                'task': monitor_task,
                'entry_time': time.time(),
                'message': warning_message
            }

    async def _handle_study_cam_exit(self, member):
        """Gerencia a saída do canal de estudo com câmera"""
        print(f"{member} saiu do canal de estudo com câmera")

        # NOVO: Parar monitoramento contínuo se estiver ativo
        if member.id in self.continuous_monitoring:
            await self._stop_continuous_monitoring(member.id)

        # NOVO: Verificar se foi expulso pelo bot
        if member.id in self.bot_kicked_members:
            print(f"{member} foi expulso pelo bot - não processando como saída voluntária")
            # Limpar da lista após um tempo para permitir nova entrada
            asyncio.create_task(self._clear_kicked_member_after_delay(member.id, 5))
            return

        if member.id in self.monitoring_members:
            monitor_info = self.monitoring_members[member.id]

            if not monitor_info['task'].done():
                monitor_info['task'].cancel()
                print(f"Task de monitoramento cancelada para {member}")

            try:
                current_embed = monitor_info['message'].embeds[0] if monitor_info['message'].embeds else None
                if current_embed and current_embed.title == "❌ Expulso do Canal":
                    print(f"Mensagem já editada para expulsão - não alterando para {member}")
                else:
                    # Calcular tempo que ficou no canal
                    time_in_channel = int(time.time() - monitor_info['entry_time'])

                    embed = discord.Embed(
                        title="👋 Saída do Canal de Estudo",
                        description=f"{member.mention} saiu do canal de estudo com câmera.",
                        color=0x87CEEB  # Azul claro
                    )
                    embed.add_field(
                        name="⏱️ Tempo no canal",
                        value=f"{time_in_channel} segundos",
                        inline=True
                    )
                    embed.add_field(
                        name="✅ Status",
                        value="Saída voluntária",
                        inline=True
                    )
                    embed.set_footer(text="Volte sempre que quiser estudar!")

                    await monitor_info['message'].edit(embed=embed, content="")

                    # Agendar deleção da mensagem após 20 segundos (sem bloquear)
                    asyncio.create_task(self._delete_message_after_delay(monitor_info['message'], 30))

            except discord.NotFound:
                print(f"Mensagem de aviso não encontrada para {member}")
            except Exception as e:
                print(f"Erro ao editar mensagem de saída: {e}")

            del self.monitoring_members[member.id]

    async def _handle_study_cam_update(self, member, after):
        """Gerencia atualizações no estado de voz no canal de estudo"""
        # Verificar se ligou câmera/transmissão durante monitoramento inicial
        if member.id in self.monitoring_members and self._has_camera_or_screen_share(after):
            print(f"{member} ligou câmera/transmissão. Cancelando monitoramento inicial.")

            monitor_info = self.monitoring_members[member.id]

            if not monitor_info['task'].done():
                monitor_info['task'].cancel()

            try:
                # Calcular tempo que levou para ligar
                time_taken = int(time.time() - monitor_info['entry_time'])
                time_remaining = self.warning_time - time_taken

                embed = discord.Embed(
                    title="🎉 Câmera/Transmissão Ligada!",
                    description=f"Perfeito, {member.mention}! Você ligou sua câmera ou transmissão de tela a tempo!",
                    color=0x00FF00  # Verde
                )

                cam_type = "📹 Câmera" if after.self_video else "🖥️ Transmissão de tela"
                embed.add_field(
                    name="✅ Tipo ativado",
                    value=cam_type,
                    inline=True
                )
                embed.add_field(
                    name="⏱️ Tempo levado",
                    value=f"{time_taken} segundos",
                    inline=True
                )
                embed.add_field(
                    name="⏰ Tempo restante",
                    value=f"{time_remaining} segundos",
                    inline=True
                )
                embed.add_field(
                    name="📚 Status",
                    value="✅ Aprovado! Continue estudando!",
                    inline=False
                )
                embed.set_footer(text="Bons estudos! 📖✨")

                await monitor_info['message'].edit(embed=embed, content="")

                # Deletar mensagem após 30 segundos
                asyncio.create_task(self._delete_message_after_delay(monitor_info['message'], 30))

            except discord.NotFound:
                pass
            except Exception as e:
                print(f"Erro ao editar mensagem de sucesso: {e}")

            del self.monitoring_members[member.id]

            # NOVO: Iniciar monitoramento contínuo
            await self._start_continuous_monitoring(member)

        # NOVO: Verificar mudanças para membros em monitoramento contínuo
        elif member.id in self.continuous_monitoring:
            if self._has_camera_or_screen_share(after):
                print(f"{member} religou câmera/transmissão - cancelando aviso contínuo")
                await self._cancel_continuous_warning(member.id)
            # Se não tem câmera/transmissão e não está sendo avisado, iniciar aviso
            elif not self.continuous_monitoring[member.id].get('warning_active', False):
                print(f"{member} desligou câmera/transmissão - iniciando aviso contínuo")
                await self._start_continuous_warning(member)

    async def _monitor_member_with_countdown(self, member, warning_message):
        """Monitora um membro com contador regressivo visual"""
        try:
            start_time = time.time()
            last_update = self.warning_time + 1  # Inicializar com valor maior para forçar primeira atualização

            while True:
                # Calcular tempo decorrido e restante
                elapsed = time.time() - start_time
                remaining = max(0, int(self.warning_time - elapsed))

                print(f"[DEBUG] {member.display_name}: Elapsed={elapsed:.1f}s, Remaining={remaining}s")

                # Se o tempo acabou, expulsar IMEDIATAMENTE
                if elapsed >= self.warning_time:
                    print(f"[DEBUG] Tempo esgotado para {member.display_name}! Expulsando...")
                    await self._kick_member_from_channel(member, warning_message)
                    return

                # Verificar se ainda precisa monitorar - MELHORADO
                try:
                    guild = self.client.get_guild(Config.ID_DO_SERVIDOR)
                    if not guild:
                        print(f"[DEBUG] Servidor não encontrado")
                        return

                    current_member = guild.get_member(member.id)
                    if not current_member:
                        print(f"[DEBUG] {member.display_name} não encontrado no servidor")
                        return

                    # Verificar se ainda está no canal
                    if not current_member.voice or not current_member.voice.channel:
                        print(f"[DEBUG] {member.display_name} não está em nenhum canal de voz")
                        return

                    if current_member.voice.channel.id != self.study_cam_channel_id:
                        print(f"[DEBUG] {member.display_name} saiu do canal de estudo")
                        return

                    # Verificar se ligou câmera/transmissão
                    if self._has_camera_or_screen_share(current_member.voice):
                        print(f"[DEBUG] {member.display_name} ligou câmera/transmissão!")
                        return

                except Exception as e:
                    print(f"[DEBUG] Erro ao verificar estado do membro: {e}")
                    return

                # Determinar se deve atualizar a mensagem - CORRIGIDO
                should_update = False
                update_intervals = [30, 20, 15, 10, 5, 3, 2, 1]

                for interval in update_intervals:
                    if remaining <= interval and last_update > interval:
                        should_update = True
                        last_update = interval
                        break

                # Atualizar mensagem se necessário
                if should_update:
                    try:
                        original_embed = warning_message.embeds[0]

                        # Criar novo embed baseado no original
                        embed = discord.Embed(
                            title=original_embed.title,
                            description=original_embed.description,
                            color=0xFF6B35 if remaining <= 10 else 0xFFD700
                        )

                        # Manter os campos originais exceto o tempo restante
                        for field in original_embed.fields:
                            if field.name != "⏰ Tempo restante":
                                embed.add_field(name=field.name, value=field.value, inline=field.inline)

                        # Atualizar campo de tempo restante
                        embed.add_field(
                            name="⏰ Tempo restante",
                            value=self._format_time_remaining(remaining),
                            inline=False
                        )

                        embed.set_thumbnail(url=original_embed.thumbnail.url if original_embed.thumbnail else None)
                        embed.set_footer(text=original_embed.footer.text if original_embed.footer else None)

                        await warning_message.edit(embed=embed)
                        print(f"[DEBUG] Mensagem atualizada para {member.display_name}: {remaining}s restantes")
                    except Exception as e:
                        print(f"Erro ao atualizar countdown: {e}")

                # Aguardar 1 segundo para próxima verificação
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            print(f"Monitoramento de {member} foi cancelado")
        except Exception as e:
            print(f"Erro durante monitoramento de {member}: {e}")
            if member.id in self.monitoring_members:
                del self.monitoring_members[member.id]

    async def _kick_member_from_channel(self, member, warning_message):
        """Expulsa o membro do canal e atualiza a mensagem - MELHORADO"""
        try:
            guild = self.client.get_guild(Config.ID_DO_SERVIDOR)
            if not guild:
                print("Servidor não encontrado")
                return

            current_member = guild.get_member(member.id)
            if not current_member:
                print(f"Membro {member} não encontrado no servidor")
                return

            # Verificar se ainda está no canal antes de tentar expulsar
            if not current_member.voice or not current_member.voice.channel:
                print(f"{current_member} não está em nenhum canal de voz")
                return

            if current_member.voice.channel.id != self.study_cam_channel_id:
                print(f"{current_member} não está mais no canal de estudo")
                return

            # Verificar se ainda não tem câmera/transmissão
            if self._has_camera_or_screen_share(current_member.voice):
                print(f"{current_member} ligou câmera/transmissão no último segundo")
                return

            print(f"Expulsando {current_member} do canal por não ligar câmera/transmissão")

            # NOVO: Marcar como expulso ANTES de fazer a expulsão
            self.bot_kicked_members.add(member.id)

            # Atualizar mensagem ANTES de expulsar
            try:
                embed = discord.Embed(
                    title="❌ Expulso do Canal",
                    description=f"{member.mention}, você foi expulso do canal [https://discord.com/channels/1013854219058544720/1380897477108039740] por não ligar sua câmera ou transmissão de tela no tempo limite.",
                    color=0xFF0000  # Vermelho
                )
                embed.add_field(
                    name="📋 Motivo",
                    value="⏰ Não ligou câmera nem transmissão em 60 segundos",
                    inline=False
                )
                embed.add_field(
                    name="🔄 Como voltar",
                    value="Você pode entrar novamente, mas lembre-se de ligar sua câmera ou transmissão!",
                    inline=False
                )
                embed.add_field(
                    name="💡 Dica",
                    value="Entre no canal e já ligue a câmera/transmissão para não ser expulso!",
                    inline=False
                )
                embed.set_footer(text="As regras do canal devem ser respeitadas 📋")

                await warning_message.edit(embed=embed, content="")
                print("Mensagem de expulsão atualizada com sucesso")

            except Exception as e:
                print(f"Erro ao editar mensagem de expulsão: {e}")

            # Expulsar membro - MÉTODOS MÚLTIPLOS PARA GARANTIR FUNCIONAMENTO
            try:
                # Método 1: move_to(None)
                await current_member.move_to(None)
                print(f"{current_member} foi desconectado do canal com move_to(None)")
            except Exception as e1:
                print(f"Erro com move_to(None): {e1}")

                try:
                    # Método 2: edit com channel=None
                    await current_member.edit(voice_channel=None)
                    print(f"{current_member} foi desconectado do canal com edit(voice_channel=None)")
                except Exception as e2:
                    print(f"Erro com edit(voice_channel=None): {e2}")

                    try:
                        # Método 3: disconnect direto
                        await current_member.voice.channel.connect().disconnect()
                        print(f"Tentativa de desconexão alternativa para {current_member}")
                    except Exception as e3:
                        print(f"Todos os métodos de expulsão falharam para {current_member}: {e1}, {e2}, {e3}")

            # Limpar do monitoramento
            if member.id in self.monitoring_members:
                del self.monitoring_members[member.id]

            # Agendar deleção da mensagem após 60 segundos
            asyncio.create_task(self._delete_message_after_delay(warning_message, 60))

        except Exception as e:
            print(f"Erro geral na expulsão de {member}: {e}")

    async def _clear_kicked_member_after_delay(self, member_id, delay_seconds):
        """Remove um membro da lista de expulsos após um delay"""
        try:
            await asyncio.sleep(delay_seconds)
            if member_id in self.bot_kicked_members:
                self.bot_kicked_members.remove(member_id)
                print(f"Membro {member_id} removido da lista de expulsos após {delay_seconds}s")
        except Exception as e:
            print(f"Erro ao limpar membro expulso: {e}")

    async def _monitor_member(self, member, warning_message):
        """Versão simplificada do monitor (mantida para compatibilidade)"""
        return await self._monitor_member_with_countdown(member, warning_message)

    async def cleanup_monitoring(self):
        """Limpa todos os monitoramentos ativos"""
        # Limpar monitoramento inicial
        for member_id, monitor_info in list(self.monitoring_members.items()):
            if not monitor_info['task'].done():
                monitor_info['task'].cancel()
            del self.monitoring_members[member_id]

        # NOVO: Limpar monitoramento contínuo
        for member_id in list(self.continuous_monitoring.keys()):
            await self._stop_continuous_monitoring(member_id)

        print("Todos os monitoramentos foram limpos")

    # NOVAS FUNÇÕES PARA MONITORAMENTO CONTÍNUO

    async def _start_continuous_monitoring(self, member):
        """Inicia o monitoramento contínuo de um membro no canal"""
        try:
            print(f"Iniciando monitoramento contínuo para {member}")
            self.continuous_monitoring[member.id] = {
                'member': member,
                'start_time': time.time(),
                'warning_active': False,
                'warning_task': None,
                'warning_message': None
            }
        except Exception as e:
            print(f"Erro ao iniciar monitoramento contínuo: {e}")

    async def _stop_continuous_monitoring(self, member_id):
        """Para o monitoramento contínuo de um membro"""
        try:
            if member_id in self.continuous_monitoring:
                monitor_info = self.continuous_monitoring[member_id]

                # Cancelar task de aviso se estiver ativa
                if monitor_info.get('warning_task') and not monitor_info['warning_task'].done():
                    monitor_info['warning_task'].cancel()

                # Deletar mensagem de aviso se existir
                if monitor_info.get('warning_message'):
                    try:
                        await monitor_info['warning_message'].delete()
                    except:
                        pass

                del self.continuous_monitoring[member_id]
                print(f"Monitoramento contínuo parado para membro ID {member_id}")
        except Exception as e:
            print(f"Erro ao parar monitoramento contínuo: {e}")

    async def _start_continuous_warning(self, member):
        """Inicia um aviso contínuo para membro sem câmera/transmissão"""
        try:
            if member.id not in self.continuous_monitoring:
                return

            warning_channel = self.client.get_channel(self.warning_channel_id)
            if not warning_channel:
                return

            embed = discord.Embed(
                title="⚠️ Câmera/Transmissão Desligada!",
                description=f"""Atenção {member.mention}! 

                Você **desligou** sua câmera/transmissão de tela no canal [https://discord.com/channels/1013854219058544720/1380897477108039740].

                **📹 ATENÇÃO:** Você tem **{self.warning_time} segundos** para **religar** sua **câmera** ou **transmissão de tela**.

                Se não ligar uma das duas opções dentro deste prazo, será automaticamente expulso do canal.""",
                color=0xFF6B35  # Laranja para re-aviso
            )

            embed.add_field(
                name="🔄 Ação necessária",
                value="Ligue sua câmera 📷 ou transmissão de tela 🖥️ **AGORA!**",
                inline=False
            )

            embed.add_field(
                name="⏰ Tempo restante",
                value=self._format_time_remaining(self.warning_time),
                inline=False
            )

            embed.set_thumbnail(
                url="https://i.postimg.cc/52m91bny/Leonardo-Phoenix-10-A-cute-cartoon-style-wolf-who-is-studying-2-removebg-preview-3.png")
            embed.set_footer(text="⚠️ Reaviso - Tribunaldo Bot | Tribunas Study")

            warning_message = await warning_channel.send(member.mention, embed=embed)

            # Iniciar task de monitoramento com countdown
            warning_task = asyncio.create_task(
                self._continuous_warning_countdown(member, warning_message)
            )

            # Atualizar informações de monitoramento
            self.continuous_monitoring[member.id].update({
                'warning_active': True,
                'warning_task': warning_task,
                'warning_message': warning_message,
                'warning_start_time': time.time()
            })

        except Exception as e:
            print(f"Erro ao iniciar aviso contínuo: {e}")

    async def _cancel_continuous_warning(self, member_id):
        """Cancela o aviso contínuo quando membro liga câmera/transmissão"""
        try:
            if member_id not in self.continuous_monitoring:
                return

            monitor_info = self.continuous_monitoring[member_id]

            if not monitor_info.get('warning_active', False):
                return

            # Cancelar task de aviso
            if monitor_info.get('warning_task') and not monitor_info['warning_task'].done():
                monitor_info['warning_task'].cancel()

            # Atualizar mensagem para sucesso
            if monitor_info.get('warning_message'):
                try:
                    member = monitor_info['member']
                    time_taken = int(time.time() - monitor_info.get('warning_start_time', time.time()))

                    embed = discord.Embed(
                        title="✅ Câmera/Transmissão Religada!",
                        description=f"Ótimo, {member.mention}! Você religou sua câmera ou transmissão a tempo!",
                        color=0x00FF00  # Verde
                    )
                    embed.add_field(
                        name="⏱️ Tempo para religar",
                        value=f"{time_taken} segundos",
                        inline=True
                    )
                    embed.add_field(
                        name="📚 Status",
                        value="✅ Continue estudando!",
                        inline=True
                    )
                    embed.set_footer(text="Mantenha sempre ligada! 📖✨")

                    await monitor_info['warning_message'].edit(embed=embed, content="")

                    # Deletar mensagem após 20 segundos
                    asyncio.create_task(
                        self._delete_message_after_delay(monitor_info['warning_message'], 30)
                    )
                except Exception as e:
                    print(f"Erro ao atualizar mensagem de sucesso contínuo: {e}")

            # Resetar estado de aviso
            self.continuous_monitoring[member_id].update({
                'warning_active': False,
                'warning_task': None,
                'warning_message': None
            })

        except Exception as e:
            print(f"Erro ao cancelar aviso contínuo: {e}")

    async def _continuous_warning_countdown(self, member, warning_message):
        """Countdown para aviso contínuo com expulsão automática"""
        try:
            start_time = time.time()
            last_update = self.warning_time + 1

            while True:
                elapsed = time.time() - start_time
                remaining = max(0, int(self.warning_time - elapsed))

                print(f"[CONTINUOUS] {member.display_name}: Elapsed={elapsed:.1f}s, Remaining={remaining}s")

                # Tempo esgotado - expulsar
                if elapsed >= self.warning_time:
                    print(f"[CONTINUOUS] Tempo esgotado para {member.display_name}! Expulsando...")
                    await self._kick_member_continuous(member, warning_message)
                    return

                # Verificar se ainda está no canal e sem câmera/transmissão
                try:
                    guild = self.client.get_guild(Config.ID_DO_SERVIDOR)
                    if not guild:
                        return

                    current_member = guild.get_member(member.id)
                    if not current_member or not current_member.voice:
                        return

                    if current_member.voice.channel.id != self.study_cam_channel_id:
                        return

                    # Se ligou câmera/transmissão, vai ser tratado em _handle_study_cam_update
                    if self._has_camera_or_screen_share(current_member.voice):
                        return

                except Exception as e:
                    print(f"[CONTINUOUS] Erro ao verificar estado: {e}")
                    return

                # Atualizar countdown na mensagem
                should_update = False
                update_intervals = [30, 20, 15, 10, 5, 3, 2, 1]

                for interval in update_intervals:
                    if remaining <= interval and last_update > interval:
                        should_update = True
                        last_update = interval
                        break

                if should_update:
                    try:
                        original_embed = warning_message.embeds[0]
                        embed = discord.Embed(
                            title=original_embed.title,
                            description=original_embed.description,
                            color=0xFF0000 if remaining <= 10 else 0xFF6B35
                        )

                        # Recriar campos exceto tempo restante
                        for field in original_embed.fields:
                            if field.name != "⏰ Tempo restante":
                                embed.add_field(name=field.name, value=field.value, inline=field.inline)

                        embed.add_field(
                            name="⏰ Tempo restante",
                            value=self._format_time_remaining(remaining),
                            inline=False
                        )

                        embed.set_thumbnail(url=original_embed.thumbnail.url if original_embed.thumbnail else None)
                        embed.set_footer(text=original_embed.footer.text if original_embed.footer else None)

                        await warning_message.edit(embed=embed)
                    except Exception as e:
                        print(f"Erro ao atualizar countdown contínuo: {e}")

                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            print(f"Aviso contínuo cancelado para {member}")
        except Exception as e:
            print(f"Erro no countdown contínuo: {e}")

    async def _kick_member_continuous(self, member, warning_message):
        """Expulsa membro por desligar câmera/transmissão durante o uso"""
        try:
            guild = self.client.get_guild(Config.ID_DO_SERVIDOR)
            if not guild:
                return

            current_member = guild.get_member(member.id)
            if not current_member or not current_member.voice:
                return

            if current_member.voice.channel.id != self.study_cam_channel_id:
                return

            if self._has_camera_or_screen_share(current_member.voice):
                return

            print(f"Expulsando {current_member} por desligar câmera/transmissão")

            # Marcar como expulso
            self.bot_kicked_members.add(member.id)

            # Atualizar mensagem
            try:
                embed = discord.Embed(
                    title="❌ Expulso - Câmera Desligada",
                    description=f"{member.mention}, você foi expulso por **desligar** sua câmera/transmissão durante o uso do canal [https://discord.com/channels/1013854219058544720/1380897477108039740].",
                    color=0xFF0000
                )
                embed.add_field(
                    name="📋 Motivo",
                    value="🔴 Desligou câmera/transmissão e não religou em 60 segundos",
                    inline=False
                )
                embed.add_field(
                    name="🔄 Como voltar",
                    value="Entre novamente e ligue a câmera/transmissão!",
                    inline=False
                )
                embed.set_footer(text="⚠️ Mantenha sempre ligada no canal de estudo!")

                await warning_message.edit(embed=embed, content="")
            except Exception as e:
                print(f"Erro ao atualizar mensagem de expulsão contínua: {e}")

            # Expulsar
            await current_member.move_to(None)

            # Limpar monitoramento
            if member.id in self.continuous_monitoring:
                del self.continuous_monitoring[member.id]

            # Deletar mensagem após 60 segundos
            asyncio.create_task(self._delete_message_after_delay(warning_message, 60))

        except Exception as e:
            print(f"Erro na expulsão contínua: {e}")

    async def _delete_message_after_delay(self, message, delay_seconds):
        """Deleta uma mensagem após um delay específico"""
        try:
            await asyncio.sleep(delay_seconds)
            await message.delete()
        except Exception as e:
            print(f"Erro ao deletar mensagem após {delay_seconds}s: {e}")

    async def get_stats(self):
        """Retorna estatísticas do sistema"""
        return {
            "active_monitoring": len(self.monitoring_members),
            "continuous_monitoring": len(self.continuous_monitoring),
            "warning_time": self.warning_time,
            "kicked_members_count": len(self.bot_kicked_members)
        }