from discord.ext import commands
from discord.ext.commands import CommandNotFound, BadArgument
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
        await ctx.channel.send(f"{ctx.author.mention} 改行/文字数が多いため削除されました", delete_after=5.0)

    # コマンド入力ミスのエラーを表示させない
    @commands.Cog.listener(name='on_command_error')
    @commands.guild_only()
    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return
        if isinstance(error, BadArgument):
            return await ctx.channel.send(f"{ctx.author.mention} 入力エラー")
        raise error


def setup(bot):
    return bot.add_cog(Sub(bot))
