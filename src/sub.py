from discord.ext import commands
from discord.ext.commands import CommandNotFound, BadArgument, MissingRole, MissingAnyRole, NoPrivateMessage
import random
import constant as cs
from multi_func import role_check_mode


class Sub(commands.Cog):
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
            await ctx.delete(delay=5)
            await ctx.channel.send(f"{ctx.author.mention} {reply[random.randint(0, 4)]}", delete_after=5)

    # コマンド入力ミスのエラーを表示させない
    @commands.Cog.listener(name='on_command_error')
    @commands.guild_only()
    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return
        elif isinstance(error, MissingRole) or isinstance(error, MissingAnyRole):
            return await ctx.channel.send(f"{ctx.author.mention} コマンドを実行できるロールを所持していません", delete_after=5)
        elif isinstance(error, NoPrivateMessage):
            return
        elif isinstance(error, BadArgument):
            return await ctx.channel.send(f"{ctx.author.mention} 入力エラー")
        raise error


def setup(bot):
    return bot.add_cog(Sub(bot))
