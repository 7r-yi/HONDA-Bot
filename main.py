import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="_", case_insensitive=True, intents=intents)

for filename in os.listdir('./src'):
    if filename.endswith('.py'):
        bot.load_extension(f'src.{filename[:-3]}')
bot.load_extension('src.zyanken.zyanken_command')
bot.load_extension('src.uno.uno_command')

bot.run(os.environ['TOKEN'])
