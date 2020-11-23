import discord
import json
import sys
from discord.ext import commands
import constant as cs
from .zyanken import zyanken_func as zf


async def run(bot, ctx):
    with open(zf.RECORD_PASS, 'w') as f:
        json.dump(zf.ZData, f, ensure_ascii=False, indent=2, separators=(',', ': '))
    await ctx.send(file=discord.File(zf.RECORD_PASS))
    data = "\n".join(zf.No_reply)
    with open(zf.REPLY_PASS, 'w') as f:
        f.write(data)
    await ctx.send(file=discord.File(zf.REPLY_PASS))
    await ctx.send("Botをシャットダウンします")
    await bot.logout()
    await sys.exit()


class Shutdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def sd(self, ctx):
        await run(self.bot, ctx)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def shutdown(self, ctx):
        await run(self.bot, ctx)


def setup(bot):
    return bot.add_cog(Shutdown(bot))
