# Comando para ativar o Modo Foco
@tree.command(guild=discord.Object(id=ID_DO_SERVIDOR), name='ativarmodofoco', description='Ativa o modo foco.')
async def ativarmodofoco(interaction: discord.Interaction):
    # Verifica se o cargo "lobo focado" existe
    role = get(interaction.guild.roles, name="lobo focado")
    if not role:
        # Se o cargo não existir, cria ele
        role = await interaction.guild.create_role(name="lobo focado", color=discord.Color.red())
        await interaction.response.send_message(
            "Cargo 'lobo focado' criado. Use o comando novamente para ativar o modo foco.", ephemeral=True)
        return

    # Verifica se o usuário já tem o cargo
    if role in interaction.user.roles:
        await interaction.response.send_message("Você já está no modo foco.", ephemeral=True)
    else:
        # Adiciona o cargo e aplica as restrições
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Modo foco ativado. Canais de texto e voz foram silenciados.",
                                                ephemeral=True)

    # Atualiza as permissões do usuário e oculta as categorias
    await atualizar_permissoes_foco(interaction.user, interaction.guild)


# Comando para desativar o Modo Foco
@tree.command(guild=discord.Object(id=ID_DO_SERVIDOR), name='desativarmodofoco', description='Desativa o modo foco.')
async def desativarmodofoco(interaction: discord.Interaction):
    # Verifica se o cargo "lobo focado" existe
    role = get(interaction.guild.roles, name="lobo focado")
    if not role:
        await interaction.response.send_message(
            "O cargo 'lobo focado' não existe. Use /ativarmodofoco para criar o cargo.", ephemeral=True)
        return

    # Verifica se o usuário já tem o cargo
    if role in interaction.user.roles:
        # Remove o cargo e restaura as permissões
        await interaction.user.remove_roles(role)
        await interaction.response.send_message("Modo foco desativado. Todas as permissões foram restauradas.",
                                                ephemeral=True)
    else:
        await interaction.response.send_message("Você não está no modo foco.", ephemeral=True)

    # Atualiza as permissões do usuário e restaura as categorias
    await atualizar_permissoes_foco(interaction.user, interaction.guild)


# Função para atualizar as permissões do usuário e ocultar/restaurar categorias
async def atualizar_permissoes_foco(member, guild):
    role = get(guild.roles, name="lobo focado")
    if not role:
        return
    # Lista de categorias que NÃO devem ser ocultadas
    categorias_nao_ocultar = ["CENTRAL 🐺", "CALLS 🌱"]

    # Itera por todas as categorias do servidor
    for category in guild.categories:
        if role in member.roles:
            # Se o usuário está no modo foco, oculta todas as categorias, exceto as especificadas
            if category.name in categorias_nao_ocultar:
                # Permite visualizar as categorias especificadas
                await category.set_permissions(member, read_messages=True, connect=True, speak=True)
            else:
                # Oculta as outras categorias
                await category.set_permissions(member, read_messages=False, connect=False, speak=False)
        else:
            # Se o usuário não está no modo foco, restaura as permissões padrão
            await category.set_permissions(member, overwrite=None)

    # Itera por todos os canais de texto e voz
    for channel in guild.channels:
        if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
            if role in member.roles:
                # Se o usuário está no modo foco, silencia todos os canais, exceto os das categorias especificadas
                if channel.category and channel.category.name in categorias_nao_ocultar:
                    # Permite interação nos canais das categorias especificadas
                    if isinstance(channel, discord.TextChannel):
                        # Silencia as notificações do canal de texto
                        await channel.set_permissions(member, read_messages=True, send_messages=True, connect=True,
                                                      speak=True, view_channel=True, mention_everyone=False)
                    else:
                        # Permite acesso ao canal de voz
                        await channel.set_permissions(member, connect=True, speak=True)
                else:
                    # Silencia os outros canais
                    await channel.set_permissions(member, read_messages=False, send_messages=True, connect=False,
                                                  speak=False)
            else:
                # Se o usuário não está no modo foco, restaura as permissões padrão
                await channel.set_permissions(member, overwrite=None)


# Evento para atualizar as permissões quando o usuário muda de canal de voz
@tribunaldo.event
async def on_voice_state_update(member, before, after):
    role = get(member.guild.roles, name="lobo focado")
    if not role:
        return

    if role in member.roles:
        if after.channel is None:  # Se o usuário saiu de um canal de voz

            # Remove o cargo "lobo focado"
            await member.remove_roles(role)

            # Adiciona um pequeno atraso para garantir que o Discord processe a remoção do cargo
            await asyncio.sleep(1)

            # Verifica novamente se o usuário ainda tem o cargo (para garantir consistência)
            if role not in member.roles:
                # Restaura as permissões
                await atualizar_permissoes_foco(member, member.guild)
        else:

            # Atualiza as permissões se o usuário mudou de canal de voz
            await atualizar_permissoes_foco(member, member.guild)