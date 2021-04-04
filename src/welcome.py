import discord
from discord.ext import commands
from datetime import datetime
from pytz import timezone
import json
import constant as cs
from multi_func import get_role
from .zyanken import zyanken_func as zf
from .uno import uno_record

RECEJT_PASS = 'src/reject_user.txt'
with open(RECEJT_PASS, 'r') as f:
    REJECT_ID = f.read().splitlines()


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
            if str(ctx.author.id) in REJECT_ID:
                await ctx.delete()
                await ctx.channel.send(f'{ctx.author.mention} コマンド実行権限がありません', delete_after=5.0)
            elif ctx.content == password:
                await ctx.delete()
                await ctx.author.add_roles(get_role(self.bot.get_guild(ctx.guild.id), cs.Visitor))
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
            time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M')
            await self.bot.get_channel(cs.Gate).send(f"{member.mention}({member}) が離脱しました ({time})")
            REJECT_ID.append(str(member.id))
            with open(RECEJT_PASS, 'w') as file:
                file.write("\n".join(REJECT_ID))
            await self.bot.get_channel(cs.Test_room).send(f"{time}\nData Output", file=discord.File(RECEJT_PASS))
        # データを削除
        if str(member.id) in zf.ZData:
            zf.ZData.pop(str(member.id))
            with open(zf.RECORD_PASS, 'w') as file2:
                json.dump(zf.ZData, file2, ensure_ascii=False, indent=2, separators=(',', ': '))
        uno_record.data_delete(str(member.id))


def setup(bot):
    return bot.add_cog(Welcome(bot))
