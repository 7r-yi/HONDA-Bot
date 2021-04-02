import discord
from discord.ext import commands
import discord.ext.commands as dec
import random
from multi_func import role_check_mode
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

    # 一般の長文を削除
    @commands.Cog.listener(name='on_message')
    @commands.guild_only()
    @commands.has_role(cs.Visitor)
    async def on_message(self, ctx):
        if ctx.channel.id != cs.General or role_check_mode(ctx) or ctx.author.bot:
            return
        if ctx.content.count("\n") < 7 and len(ctx.content) < 400:
            return
        await ctx.delete()
        await ctx.channel.send(f"{ctx.author.mention} 改行/文字数が多いため削除されました", delete_after=5)

    # Botにメンションしたら返答
    @commands.Cog.listener(name='on_message')
    @commands.guild_only()
    @commands.has_role(cs.Visitor)
    async def on_message(self, ctx):
        if cs.Honda in ctx.raw_mentions and not ctx.author.bot:
            reply = ["うるさい", "話しかけてこないでくれませんか？", "YOU LOSE 俺の勝ち", "メンションするな", "不敬罪ですよ"]
            await ctx.channel.send(f"{ctx.author.mention} {reply[random.randint(0, 4)]}", delete_after=5)

    # ケイスケホンダ宛てのDMを出力
    @commands.Cog.listener(name='on_message')
    @commands.has_role(cs.Visitor)
    async def on_message(self, ctx):
        if ctx.author.bot or type(ctx.channel) != discord.DMChannel:
            return
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
        msg = f"{ctx.author} が、ケイスケホンダに {ctx.content} とDMを送信しました ({time})"
        if len(msg) > 2000:
            msg = f"{ctx.author} が、ケイスケホンダに {ctx.content[:100]}(文字数が多すぎるため略) とDMを送信しました ({time})"
        await self.bot.get_channel(cs.Mod_room).send(msg)

    # コマンド入力ミスのエラーを表示させない
    @commands.Cog.listener(name='on_command_error')
    @commands.guild_only()
    async def on_command_error(self, ctx, error):
        if isinstance(error, dec.CommandNotFound) or isinstance(error, dec.CommandInvokeError):
            return
        elif isinstance(error, dec.MissingRole) or isinstance(error, dec.MissingAnyRole):
            return await ctx.channel.send(f"{ctx.author.mention} コマンドを実行できるロールを所持していません", delete_after=5)
        elif isinstance(error, dec.NoPrivateMessage):
            return
        elif isinstance(error, dec.BadArgument):
            return await ctx.channel.send(f"{ctx.author.mention} 入力エラー")
        raise error

    # メンション先にメッセージを送信する
    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def send(self, ctx, to_id=None, *msg):
        await run_send(self.bot, ctx, to_id, *msg)


def setup(bot):
    return bot.add_cog(Talk(bot))
