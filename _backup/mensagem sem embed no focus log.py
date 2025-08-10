import asyncio
import discord
from discord import app_commands
from discord.utils import get
from constants import TOKEN, ID_DO_SERVIDOR

class client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False # Nós usamos isso para o bot não sincronizar os comandos mais de uma vez

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced: #Checar se os comandos slash foram sincronizados
            await tree.sync(guild = discord.Object(id=ID_DO_SERVIDOR))
            self.synced = True
        print(f"Entramos como {self.user}.")


tribunaldo = client()
tree = app_commands.CommandTree(tribunaldo)

# DESPERTAR
@tree.command(guild = discord.Object(id=ID_DO_SERVIDOR), name = 'despertar', description='teste')
async def despertar(interaction: discord.Interaction):
    await interaction.response.send_message("Estou funcionando! AUUUUU", ephemeral = False)

# EMBED - CARGOS DE HORAS
@tree.command(guild = discord.Object(id=ID_DO_SERVIDOR),
              name = 'embed',
              description='Exibe os cargos de horas do servidor.')
async def embed(interaction: discord.Interaction):
    embed_cargos = discord.Embed(
        title = 'Cargos e Quantidade de Horas do Tribunas',
        description= '''Para conseguir os cargos abaixo, basta você entrar em um canal de voz e ficar lá pela quantidade de horas necessárias para cada cargo. 
        
        As horas são cumulativas, ou seja, se você sair do canal quando tiver 1 hora, quando entrar novamete as horas continuarão a ser contadas de onde parou.''',
        colour = 9055202
    )
    embed_cargos.set_author(
        name="", 
        icon_url="https://i.postimg.cc/XJq8hkd0/Design-sem-nome-1.png", 
        )
    embed_cargos.set_thumbnail(url="https://i.postimg.cc/XJq8hkd0/Design-sem-nome-1.png")
    
    embed_cargos.set_image(url="https://i.postimg.cc/BnCdHs07/Leonardo-Phoenix-10-A-cute-cartoon-style-gray-wolf-that-is-wea-3-1.jpg")
    
    embed_cargos.set_footer(text="Espero você nos canais de voz!")

    embed_cargos.add_field(name="lobinho recruta", value="24h", inline=True)

    await interaction.response.send_message(embed=embed_cargos)

# MODO FOCO
@tribunaldo.event
async def on_voice_state_update(member, before, after):
    FOCUS_CHANNEL_NAME = "┊⛔ Foco Extremo"
    CATEGORIES_NOT_HIDE = ["CENTRAL 🐺", "CALLS 🌱"]
    guild = tribunaldo.get_guild(ID_DO_SERVIDOR)
    FOCUS_LOG_CHANNEL = tribunaldo.get_channel(1331925564268744776)

    # Obtém o canal de voz em que o usuário está atualmente
    voice_channel = member.voice.channel if member.voice else None
    categoria_atual = voice_channel.category if voice_channel else None

    # SE O MEMBRO ENTRA NO CANAL DE VOZ
    if before.channel is None and after.channel is not None and after.channel.name == FOCUS_CHANNEL_NAME:
        print(f"{member} entrou no canal de voz {after.channel.name}")
        await FOCUS_LOG_CHANNEL.send(f"Modo foco ATIVADO, {member.mention}! Todos os canais de textos estarão ocultados enquanto você estiver no canal {after.channel.mention}.Para voltar a visualizá-los, basta sair do canal.Bons estudos!")

        for category in guild.categories:
            if category.name not in CATEGORIES_NOT_HIDE:
                await category.set_permissions(member, view_channel=False)  # Oculta a categoria

        for channel in guild.channels:
            if channel.category and channel.category.name not in CATEGORIES_NOT_HIDE:
                await channel.set_permissions(member, view_channel=False)  # Oculta o canal

    # SE O MEMBRO SAI DO CANAL DE VOZ
    if before.channel is not None and after.channel is None and before.channel.name == FOCUS_CHANNEL_NAME:
        print(f"{member} saiu do canal de voz {before.channel.name}")
        await FOCUS_LOG_CHANNEL.send(f"Modo foco DESATIVADO, {member.mention}! Os canais de textos ocultos estão voltando a ser visualizados agora. Como o servidor possui muitos canais, deve durar cerca de 20 segundos.  Obrigado pela paciência!")


        for category in guild.categories:
            await category.set_permissions(member, overwrite=None)  # Remove as permissões personalizadas

        for channel in guild.channels:
            await channel.set_permissions(member, overwrite=None)  # Remove as permissões personalizadas

# ENVIAR MENSAGENS NA DM OU CANAL
@tree.command(guild = discord.Object(id=ID_DO_SERVIDOR), name="dm", description="Envia uma dm pra um usuário")
@app_commands.describe(user="O usuário que vai receber a mensagem", message="A mensagem a ser enviada")
async def dm(interaction: discord.Interaction, user: discord.User, message: str):
    try:
        await user.send(message)
        await interaction.response.send_message(f"Mensagem enviada para {user.name}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Não posso enviar a mensagem. DMs bloqueadas?", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Ocorreu um erro: {e}", ephemeral=True)


tribunaldo.run(TOKEN)