import discord
from discord.ext import commands
from constants.constants_qa import TOKEN

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix="!", case_insensitive = True, intents=intents)


@client.command()
async def ola(ctx):
    await ctx.send("AUUUUUU! Iae! Eu sou o Tribunaaaaldo!")

client.run(TOKEN)