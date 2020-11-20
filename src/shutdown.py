import discord
import json
import sys
from discord.ext import commands
import constant as cs
from .zyanken import zyanken_func


async def run(bot, ctx):
    with open('zyanken/zyanken_record.json', 'w') as f:
        json.dump(zyanken_func.Zyanken_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
    await ctx.send(file=discord.File('zyanken/zyanken_record.json'))
    await ctx.send("Botをシャットダウンします")
    await bot.logout()
    await sys.exit()


class Shutdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def sd(self, bot, ctx):
        await run(bot, ctx)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def shutdown(self, bot, ctx):
        await run(bot, ctx)


def setup(bot):
    return bot.add_cog(Shutdown(bot))
