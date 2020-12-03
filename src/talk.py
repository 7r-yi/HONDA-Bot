from discord.ext import commands
import re
import constant as cs


async def run_say(guild, ctx, channel_id, msg):
    if channel_id is None:
        return await ctx.send(f"{ctx.author.mention} 送信先チャンネルをメンションしてください")
    elif msg is None:
        return await ctx.send(f"{ctx.author.mention} 送信メッセージを入力してください")

    try:
        await guild.get_channel(int(re.sub('[^0-9]', "", channel_id))).send(msg)
    except AttributeError:
        return await ctx.send(f"{ctx.author.mention} 入力エラー")
    await ctx.send(f"{ctx.author.mention} 送信しました")


async def run_sendDM(bot, ctx, user_id, msg):
    if user_id is None:
        return await ctx.send(f"{ctx.author.mention} 送信先ユーザーをメンションしてください")
    elif msg is None:
        return await ctx.send(f"{ctx.author.mention} 送信メッセージを入力してください")

    try:
        await bot.get_user(int(re.sub('[^0-9]', "", user_id))).send(msg)
    except AttributeError:
        return await ctx.send(f"{ctx.author.mention} 入力エラー")
    await ctx.send(f"{ctx.author.mention} 送信しました")


class Talk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def say(self, ctx, channel_id=None, msg=None):
        await run_say(self.bot.get_guild(cs.Server), ctx, channel_id, msg)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def sdm(self, ctx, user_id=None, msg=None):
        await run_sendDM(self.bot, ctx, user_id, msg)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def senddm(self, ctx, user_id=None, msg=None):
        await run_sendDM(self.bot, ctx, user_id, msg)


def setup(bot):
    return bot.add_cog(Talk(bot))
