import discord
from discord import app_commands
from constants.constants_prod import Config


def setup_tribunaldo_chat_bot(tree, tribunaldo_chat_bot):
    """Configura os comandos slash relacionados ao chat bot Gemini"""

    # Conversar com o bot via slash command
    @tree.command(name="chat",
                  description="Conversa com o Tribunaldo usando IA",
                  guild=discord.Object(id=Config.ID_DO_SERVIDOR))
    @app_commands.describe(message="Sua mensagem para o Tribunaldo")
    async def chat(interaction: discord.Interaction, message: str):
        """"""
        print(f"Comando /chat chamado por {interaction.user} com mensagem: {message}")

        # Verificar se o módulo Gemini está funcionando
        if not tribunaldo_chat_bot.model:
            await interaction.response.send_message(
                "❌ Sistema de chat temporariamente indisponível. Tente mencionar @Tribunaldo em uma mensagem normal! AUUUUU! 🐺",
                ephemeral=True
            )
            return

        # Verificar cooldown
        if tribunaldo_chat_bot._is_user_on_cooldown(interaction.user.id):
            remaining_time = tribunaldo_chat_bot.cooldown_time - (
                    discord.utils.utcnow().replace(tzinfo=None) - tribunaldo_chat_bot.user_cooldowns[interaction.user.id]
            ).total_seconds()
            await interaction.response.send_message(
                f"🕐 Calma aí, {interaction.user.mention}! Aguarde mais {remaining_time:.1f} segundos antes de usar o chat novamente. AUUUUU! 🐺",
                ephemeral=True
            )
            return

        # Deferir a resposta para ter mais tempo
        await interaction.response.defer()

        # Atualizar cooldown
        tribunaldo_chat_bot._update_user_cooldown(interaction.user.id)

        try:
            # Gerar resposta
            response = await tribunaldo_chat_bot.generate_response(
                message,
                interaction.user.id,
                interaction.user.display_name
            )

            # Enviar resposta
            if len(response) > 2000:
                # Se muito longa, enviar primeira parte e o resto como followup
                first_part = response[:2000]
                remaining = response[2000:]

                await interaction.followup.send(first_part)

                # Dividir o restante em chunks se necessário
                chunks = [remaining[i:i + 2000] for i in range(0, len(remaining), 2000)]
                for chunk in chunks:
                    await interaction.followup.send(chunk)
            else:
                await interaction.followup.send(response)

        except Exception as e:
            print(f"Erro no comando /chat: {e}")
            await interaction.followup.send(
                "❌ Ops! Algo deu errado ao processar sua mensagem. Tente novamente! AUUUUU! 🐺"
            )


    # Limpar o histórico de conversa do usuário
    @tree.command(name="chat_limpar", description="Limpa seu histórico de conversa com o Tribunaldo",
                  guild=discord.Object(id=Config.ID_DO_SERVIDOR))
    async def chat_limpar(interaction: discord.Interaction):
        print(f"Comando /chat_limpar chamado por {interaction.user}")

        success = await tribunaldo_chat_bot.clear_user_history(interaction.user.id)

        if success:
            embed = discord.Embed(
                title="🧹 Histórico Limpo!",
                description="Seu histórico de conversa com o Tribunaldo foi limpo com sucesso! AUUUUU! 🐺",
                color=9055202
            )
            embed.set_thumbnail(
                url="https://i.postimg.cc/3JZsg5Xk/Leonardo-Phoenix-10-A-cute-gray-wolf-in-cartoon-style-is-with-2.jpg")
        else:
            embed = discord.Embed(
                title="📝 Sem Histórico",
                description="Você ainda não tem histórico de conversa para limpar! Que tal começar uma conversa? AUUUUU! 🐺",
                color=9055202
            )
            embed.set_thumbnail(
                url="https://i.postimg.cc/3JZsg5Xk/Leonardo-Phoenix-10-A-cute-gray-wolf-in-cartoon-style-is-with-2.jpg")

        await interaction.response.send_message(embed=embed, ephemeral=True)


    # Mostrar estatísticas de conversa do usuário
    @tree.command(name="chat_stats", description="Mostra suas estatísticas de conversa com o Tribunaldo",
                  guild=discord.Object(id=Config.ID_DO_SERVIDOR))
    async def chat_stats(interaction: discord.Interaction):
        print(f"Comando /chat_stats chamado por {interaction.user}")

        stats = await tribunaldo_chat_bot.get_user_stats(interaction.user.id)

        if not stats:
            embed = discord.Embed(
                title="📊 Estatísticas de Chat",
                description="Você ainda não conversou comigo! Que tal começar uma conversa usando `/chat` ou me mencionando? AUUUUU! 🐺",
                color=9055202
            )
        else:
            embed = discord.Embed(
                title="📊 Suas Estatísticas de Chat",
                description=f"Aqui estão suas estatísticas de conversa comigo, {interaction.user.mention}! AUUUUU! 🐺",
                color=9055202
            )

            embed.add_field(
                name="💬 Mensagens Enviadas",
                value=str(stats["user_messages"]),
                inline=True
            )
            embed.add_field(
                name="🤖 Respostas Recebidas",
                value=str(stats["bot_responses"]),
                inline=True
            )
            embed.add_field(
                name="🔄 Total de Interações",
                value=str(stats["total_interactions"]),
                inline=True
            )

            if stats["last_interaction"]:
                from datetime import datetime
                last_time = datetime.fromisoformat(stats["last_interaction"])
                embed.add_field(
                    name="🕒 Última Conversa",
                    value=f"<t:{int(last_time.timestamp())}:R>",
                    inline=False
                )

        embed.set_thumbnail(
            url="https://i.postimg.cc/3JZsg5Xk/Leonardo-Phoenix-10-A-cute-gray-wolf-in-cartoon-style-is-with-2.jpg")
        embed.set_footer(
            text=f"Canal dedicado: #{Config.Channels.ID_CANAL_CHAT_TRIBUNALDO} | Use /chat em outros canais!")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Mostrar informações de ajuda sobre o chat bot
    @tree.command(name="chat_ajuda", description="Mostra como usar o chat bot do Tribunaldo",
                  guild=discord.Object(id=Config.ID_DO_SERVIDOR))
    async def chat_ajuda(interaction: discord.Interaction):

        print(f"Comando /chat_ajuda chamado por {interaction.user}")

        embed = discord.Embed(
            title="🤖 Como Conversar com o Tribunaldo",
            description="Aqui estão todas as formas de conversar comigo! AUUUUU! 🐺",
            color=9055202
        )

        embed.add_field(
            name="💬 Como Conversar",
            value=f"""
            **Canal Dedicado:** <#{Config.Channels.ID_CANAL_CHAT_TRIBUNALDO}>
            • Envie qualquer mensagem lá que eu respondo!

            **Outros Canais:**
            • Me mencione: `@Tribunaldo oi!`
            • Use o comando: `/chat <mensagem>`
            """,
            inline=False
        )

        embed.add_field(
            name="⚡ Funcionalidades",
            value="""
            • Histórico de conversa personalizado
            • Respostas contextualizadas
            • Cooldown de 5 segundos entre mensagens
            • Máximo de 10 mensagens no histórico
            """,
            inline=False
        )

        embed.add_field(
            name="🔧 Comandos Úteis",
            value="""
            `/chat_limpar` - Limpa seu histórico
            `/chat_stats` - Suas estatísticas
            `/chat_ajuda` - Esta mensagem
            """,
            inline=False
        )

        embed.add_field(
            name="💡 Dicas",
            value=f"No canal <#{Config.Channels.ID_CANAL_CHAT_TRIBUNALDO}> você pode conversar comigo naturalmente! Em outros canais, me mencione. Sou especialista em motivação para estudos! 🎓",
            inline=False
        )

        embed.set_thumbnail(
            url="https://i.postimg.cc/3JZsg5Xk/Leonardo-Phoenix-10-A-cute-gray-wolf-in-cartoon-style-is-with-2.jpg")
        embed.set_footer(text="Desenvolvido com ❤️ para ajudar nos seus estudos!")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    print("✅ Comandos do Gemini Chat configurados com sucesso!")