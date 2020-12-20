import discord
from discord.ext import commands
from datetime import datetime
from pytz import timezone
import re
import constant as cs


# メンション先にメッセージを送信する
async def run_send(bot, ctx, to_id, *msg):
    if to_id is None or re.sub('[^0-9]', "", to_id) == "":
        return await ctx.send(f"{ctx.author.mention} 送信先をメンションしてください", delete_after=10)
    elif not msg:
        return await ctx.send(f"{ctx.author.mention} 送信メッセージを入力してください", delete_after=10)

    guild = bot.get_guild(ctx.guild.id)
    id = int(re.sub('[^0-9]', "", to_id))
    try:
        await guild.get_channel(id).send(" ".join(msg))
    except AttributeError:
        try:
            await bot.get_user(id).send(" ".join(msg))
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
        name = self.bot.get_guild(ctx.guild.id).get_member(ctx.author.id)
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
        msg = f"{name.mention}が、ケイスケホンダに {ctx.content} とDMを送信しました ({time})"
        await self.bot.get_channel(cs.Mod_room).send(msg)

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def send(self, ctx, to_id=None, *msg):
        await run_send(self.bot, ctx, to_id, *msg)


def setup(bot):
    return bot.add_cog(Talk(bot))
