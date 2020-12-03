import discord
from discord.ext import commands
from datetime import datetime
from pytz import timezone
import re
import constant as cs


# 特定のテキストチャンネルにて発言させる
async def run_say(guild, ctx, channel_id, *msg):
    if channel_id is None:
        return await ctx.send(f"{ctx.author.mention} 送信先チャンネルをメンションしてください", delete_after=5)
    elif not msg:
        return await ctx.send(f"{ctx.author.mention} 送信メッセージを入力してください", delete_after=5)

    try:
        await guild.get_channel(int(re.sub('[^0-9]', "", channel_id))).send(" ".join(msg))
    except AttributeError:
        return await ctx.send(f"{ctx.author.mention} 入力エラー", delete_after=5)
    await ctx.send(f"{ctx.author.mention} 送信しました", delete_after=5)


# 特定のユーザーにDMを送る
async def run_sendDM(bot, ctx, user_id, *msg):
    if user_id is None:
        return await ctx.send(f"{ctx.author.mention} 送信先ユーザーをメンションしてください", delete_after=5)
    elif not msg:
        return await ctx.send(f"{ctx.author.mention} 送信メッセージを入力してください", delete_after=5)

    try:
        await bot.get_user(int(re.sub('[^0-9]', "", user_id))).send(" ".join(msg))
    except AttributeError:
        return await ctx.send(f"{ctx.author.mention} 入力エラー", delete_after=5)
    await ctx.send(f"{ctx.author.mention} 送信しました", delete_after=5)


class Talk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ケイスケホンダ宛てのDMを出力
    @commands.Cog.listener(name='on_message')
    @commands.has_role(cs.Visitor)
    async def on_message(self, ctx):
        if ctx.author.bot or type(ctx.channel) != discord.DMChannel:
            return
        name = self.bot.get_guild(cs.Server).get_member(ctx.author.id)
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
        msg = f"{name.mention}が、ケイスケホンダに {ctx.content} とDMを送信しました ({time})"
        await self.bot.get_channel(cs.Mod_room).send(msg)

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def say(self, ctx, channel_id=None, *msg):
        await run_say(self.bot.get_guild(cs.Server), ctx, channel_id, *msg)

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def sdm(self, ctx, user_id=None, *msg):
        await run_sendDM(self.bot, ctx, user_id, *msg)

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def senddm(self, ctx, user_id=None, *msg):
        await run_sendDM(self.bot, ctx, user_id, *msg)


def setup(bot):
    return bot.add_cog(Talk(bot))
