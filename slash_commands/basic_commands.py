import discord
from discord import app_commands
from constants.constants_prod import Config

def setup_commands(tree):
    """Configura todos os comandos slash do bot"""
    
    @tree.command(name="despertar", description="verifica se o tribunaldo está acordado", guild=discord.Object(id=Config.ID_DO_SERVIDOR))
    async def despertar(interaction: discord.Interaction):
        print(f"Comando /despertar chamado por {interaction.user}")
        await interaction.response.send_message("Estou funcionando! AUUUUU 🐺", ephemeral=False)

    # Comando de sync comentado - descomente se necessário
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

    # Adicione aqui outros comandos slash conforme necessário
    # Exemplo de comando adicional:
    # @tree.command(name="ajuda", description="Mostra informações de ajuda", guild=discord.Object(id=Config.ID_DO_SERVIDOR))
    # async def ajuda(interaction: discord.Interaction):
    #     embed = discord.Embed(
    #         title="Comandos Disponíveis",
    #         description="Lista de comandos do Tribunaldo",
    #         color=9055202
    #     )
    #     embed.add_field(name="/despertar", value="Verifica se o bot está funcionando", inline=False)
    #     await interaction.response.send_message(embed=embed, ephemeral=True)