import discord
from discord.ext import tasks, commands
import jaconv
from datetime import datetime
from pytz import timezone
import json
import constant as cs
from multi_func import get_role, role_check_mode
from . import zyanken_func as zf


async def run_noreply(guild, ctx, name):
    if ctx.channel.id != cs.Zyanken_room:
        return

    if name is None:
        name = guild.get_member(ctx.author.id).display_name
    for member in get_role(guild, cs.Visitor).members:
        if name.lower() == member.display_name.lower():
            if str(member.id) not in zf.No_reply:
                zf.No_reply.append(str(member.id))
                await ctx.send(f"{guild.get_member(member.id).mention} 返信を無効にしました")
            else:
                await ctx.send(f"{ctx.author.mention} 既に返信が無効になっています")
            return
    await ctx.send(f"{ctx.author.mention} ユーザーが見つかりませんでした")


async def run_noreplycancel(guild, ctx, name):
    if ctx.channel.id != cs.Zyanken_room:
        return

    if name is None:
        name = guild.get_member(ctx.author.id).display_name
    for member in get_role(guild, cs.Visitor).members:
        if name.lower() == member.display_name.lower():
            if str(member.id) in zf.No_reply:
                zf.No_reply.remove(str(member.id))
                await ctx.send(f"{guild.get_member(member.id).mention} 返信を有効にしました")
            else:
                await ctx.send(f"{ctx.author.mention} 既に返信は有効になっています")
            return
    await ctx.send(f"{ctx.author.mention} ユーザーが見つかりませんでした")


async def run_stats(bot, guild, ctx, name):
    # じゃんけん会場のみ反応(モデレーター以外)
    if ctx.channel.id != cs.Zyanken_room and not role_check_mode(ctx):
        return

    if name is None:
        name = guild.get_member(ctx.author.id).display_name
    data, user, id = None, None, None
    for member in get_role(guild, cs.Visitor).members:
        if name.lower() == member.display_name.lower():
            if str(member.id) in zf.ZData:
                data = zf.stats_output(member.id)
                user, id = member.display_name, member.id
            else:
                await ctx.send(f"{ctx.author.mention} データが記録されていません")
                return
    if name == "ケイスケホンダ" and data is None and id is None:
        data = zf.stats_output(cs.Honda)
        user, id = name, cs.Honda
    elif data is None and id is None:
        await ctx.send(f"{ctx.author.mention} データが見つかりませんでした")
        return

    embed = discord.Embed(title=user, color=0x4169E1)
    embed.set_author(name='Stats', icon_url=bot.get_user(id).avatar_url)
    embed.set_thumbnail(url=data[6])
    embed.add_field(name="勝率", value=f"{data[2]:.02f}% ({data[0] + data[1]}戦 {data[0]}勝{data[1]}敗)", inline=False)
    embed.add_field(name="グー勝ち", value=f"{data[3][0]}回")
    embed.add_field(name="チョキ勝ち", value=f"{data[3][1]}回")
    embed.add_field(name="パー勝ち", value=f"{data[3][2]}回")
    embed.add_field(name="グー負け", value=f"{data[4][0]}回")
    embed.add_field(name="チョキ負け", value=f"{data[4][1]}回")
    embed.add_field(name="パー負け", value=f"{data[4][2]}回")
    embed.add_field(name="連勝数", value=f"最大{data[5][1]}連勝 (現在{data[5][0]}連勝中)")
    await ctx.send(embed=embed)


async def update_roles(guild, winner, loser):
    role_W, role_L = get_role(guild, cs.Winner), get_role(guild, cs.Loser)
    if winner != zf.Former_winner:
        for i in range(len(winner)):
            if winner[i] not in zf.Former_winner:
                await guild.get_member(winner[i]).add_roles(role_W)
        for i in range(len(zf.Former_winner)):
            if zf.Former_winner[i] not in winner:
                await guild.get_member(zf.Former_winner[i]).remove_roles(role_W)
        zf.Former_winner = winner
    if loser != zf.Former_loser:
        for i in range(len(loser)):
            if loser[i] not in zf.Former_loser:
                await guild.get_member(loser[i]).add_roles(role_L)
        for i in range(len(zf.Former_loser)):
            if zf.Former_loser[i] not in loser:
                await guild.get_member(zf.Former_loser[i]).remove_roles(role_L)
        zf.Former_loser = loser


async def run_ranking(guild, ctx, type, num):
    if ctx.channel.id != cs.Zyanken_room and not role_check_mode(ctx):
        return
    elif type.lower() not in ["wm", "winsmax", "wma", "winsmaxall"] or not isinstance(num, int):
        return await ctx.send(f"{ctx.author.mention} 入力形式が間違っています\n"
                              ">>> **_RanKing Type N**\nType = WinsMax / WinsMaxAll\n"
                              "N : 上位N名を表示 (未入力/範囲外の場合 : 対象者全員)")

    type = "winsmaxall" if type.lower() in ["wma", "winsmaxall"] else "winsmax"
    title, stc, winner, loser = zf.ranking_output(guild, type)
    if len(stc) == 0:
        await ctx.send("現在、対象者はいません")
        return
    await ctx.send(f"じゃんけん戦績ランキング【{title}】")
    stc_split, i = stc.split("\n"), 0
    stc_split.append("")
    send_times = num if 1 <= num < len(stc_split) else len(stc_split) - 1
    while i < send_times:  # 2000文字以下に分割して送信
        msg, length = "", len(stc_split[i]) + 1
        while all([length < 1990, i < send_times]):
            msg += stc_split[i] + "\n"
            length += len(stc_split[i + 1]) + 1
            i += 1
        await ctx.send(f"```{msg}```")

    if type == "winsmax":
        await update_roles(guild, winner, loser)


async def run_statssave(ctx):
    with open(zf.RECORD_PASS, 'w') as f:
        json.dump(zf.ZData, f, ensure_ascii=False, indent=2, separators=(',', ': '))
    data = "\n".join(zf.No_reply)
    with open(zf.REPLY_PASS, 'w') as f:
        f.write(data)
    await ctx.send(file=discord.File(zf.RECORD_PASS))
    await ctx.send(file=discord.File(zf.REPLY_PASS))
    time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
    await ctx.send(f"全戦績データを出力＆セーブしました ({time})")


class Zyanken(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 現在のWinner/Loserロールを取得
    @commands.Cog.listener()
    async def on_ready(self):
        _, _, winner, loser = zf.ranking_output(self.bot.get_guild(cs.Server), type="winsmax")
        zf.Former_winner, zf.Former_loser = winner, loser
        self.role_update.start()
        self.data_auto_save.start()

    # 定期的にWinner/Loserロール更新
    @tasks.loop(minutes=5)
    async def role_update(self):
        _, _, winner, loser = zf.ranking_output(self.bot.get_guild(cs.Server), type="winsmax")
        await update_roles(self.bot.get_guild(cs.Server), winner, loser)

    # 定期的にデータをオートセーブ
    @tasks.loop(minutes=1)
    async def data_auto_save(self):
        with open(zf.RECORD_PASS, 'r') as f:
            before_zdata = json.load(f)
        if zf.ZData != before_zdata:
            if zf.File_backup is not None:
                await zf.File_backup.delete()
            with open(zf.RECORD_PASS, 'w') as f:
                json.dump(zf.ZData, f, ensure_ascii=False, indent=2, separators=(',', ': '))
            time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
            zf.File_backup = await self.bot.get_channel(cs.Test_room).send(
                f"{time}\nData Auto Saved", file=discord.File(zf.RECORD_PASS))
        data = "\n".join(zf.No_reply)
        with open(zf.REPLY_PASS, 'w') as f:
            f.write(data)

    @commands.Cog.listener(name='on_message')
    @commands.guild_only()
    @commands.has_role(cs.Visitor)
    async def on_message(self, ctx):
        if ctx.author.bot:
            return
        if all([ctx.channel.id != cs.Zyanken_room, ctx.channel.id != cs.Test_room]):
            return

        for hand in ["グー", "チョキ", "パー"]:
            # グー,チョキ,パーの順に文字が含まれているか検索
            if hand in jaconv.hira2kata(jaconv.h2z(ctx.content)):
                img, hand, msg, emoji1, emoji2 = zf.honda_to_zyanken(hand, ctx.author.id)
                if str(ctx.author.id) not in zf.No_reply:
                    await ctx.add_reaction(emoji1)
                    await ctx.add_reaction(emoji2)
                    await ctx.channel.send(f"{ctx.author.mention} {hand}\n**{msg}**",
                                           file=discord.File(img), delete_after=5.0)
                if cs.Zyanken not in [roles.id for roles in ctx.author.roles]:
                    guild = self.bot.get_guild(cs.Server)
                    await guild.get_member(ctx.author.id).add_roles(get_role(guild, cs.Zyanken))
                break

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def nr(self, ctx, name=None):
        await run_noreply(self.bot.get_guild(cs.Server), ctx, name)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def noreply(self, ctx, name=None):
        await run_noreply(self.bot.get_guild(cs.Server), ctx, name)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def nrc(self, ctx, name=None):
        await run_noreplycancel(self.bot.get_guild(cs.Server), ctx, name)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def noreplycancel(self, ctx, name=None):
        await run_noreplycancel(self.bot.get_guild(cs.Server), ctx, name)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def st(self, ctx, name=None):
        await run_stats(self.bot, self.bot.get_guild(cs.Server), ctx, name)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def stats(self, ctx, name=None):
        await run_stats(self.bot, self.bot.get_guild(cs.Server), ctx, name)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def rk(self, ctx, type="winsmax", num=999):
        await run_ranking(self.bot.get_guild(cs.Server), ctx, type, num)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def ranking(self, ctx, type="winsmax", num=999):
        await run_ranking(self.bot.get_guild(cs.Server), ctx, type, num)

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def ss(self, ctx):
        await run_statssave(ctx)

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def statssave(self, ctx):
        await run_statssave(ctx)


def setup(bot):
    return bot.add_cog(Zyanken(bot))
