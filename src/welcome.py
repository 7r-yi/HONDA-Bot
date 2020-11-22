from discord.ext import commands
from datetime import datetime
from pytz import timezone
import json
import constant as cs
from multi_func import get_role
from .zyanken import zyanken_func as zf
from .uno import uno_record


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Gateでの入力チェック
    @commands.Cog.listener(name='on_message')
    @commands.guild_only()
    async def on_message(self, ctx):
        if ctx.channel.id == cs.Gate and not ctx.author.bot:
            time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo'))
            password = f"_join {time.strftime('%Y/%m/%d')}"
            if ctx.content == password:
                await ctx.delete()
                await ctx.author.add_roles(get_role(self.bot.get_guild(cs.Server), cs.Visitor))
                await ctx.channel.send(f"{ctx.author.mention} 参加しました ({time.strftime('%Y/%m/%d %H:%M')})")
            else:
                await ctx.delete(delay=5.0)
                await ctx.channel.send(f'{ctx.author.mention} コマンドが違います', delete_after=5.0)

    @commands.Cog.listener(name='on_member_join')
    async def on_member_join(self, member):
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M')
        await self.bot.get_channel(cs.Gate).send(f"{member.mention} が入室しました ({time})")

    @commands.Cog.listener(name='on_member_remove')
    async def on_member_remove(self, member):
        if cs.Visitor in [role.id for role in member.roles]:
            await member.ban(delete_message_days=0)
            time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M')
            await self.bot.get_channel(cs.Gate).send(f"{member.mention}({member}) を削除しました ({time})")
        # データを削除
        if str(member.id) in zf.ZData:
            zf.ZData.pop(str(member.id))
            with open(zf.RECORD_PASS, 'w') as f:
                json.dump(zf.ZData, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        uno_record.data_delete(str(member.id))


def setup(bot):
    return bot.add_cog(Welcome(bot))
