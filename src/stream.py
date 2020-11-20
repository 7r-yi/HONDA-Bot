from discord.ext import commands
import random
import constant as cs
from multi_func import get_role


# 参加希望を出す
async def run_can(ctx):
    if ctx.channel.id != cs.Recruit:
        return

    if ctx.author.id not in cs.Joiner:
        cs.Joiner.append(ctx.author.id)
        await ctx.send(f'{ctx.author.mention} 参加希望者リストに追加しました', delete_after=5.0)
    else:
        await ctx.send(f'{ctx.author.mention} すでに参加希望が出されています', delete_after=5.0)


# 参加希望を取り消す
async def run_drop(ctx):
    if ctx.channel.id != cs.Recruit:
        return

    if ctx.author.id in cs.Joiner:
        cs.Joiner.remove(ctx.author.id)
        await ctx.send(f'{ctx.author.mention} 参加希望を取り消しました', delete_after=5.0)
    else:
        await ctx.send(f'{ctx.author.mention} 参加希望が出されていません', delete_after=5.0)


# 参加者を削除する
async def run_remove(guild, ctx, name):
    if name is None:
        return await ctx.send("ユーザー名を入力してください")

    for member in get_role(guild, cs.Visitor).members:
        if name.lower() == member.display_name.lower():
            if str(member.id) in cs.Joiner:
                cs.Joiner.remove(member.id)
                return await ctx.send(f"{member.display_name}を削除しました")
            else:
                return await ctx.send(f"{member.display_name}は参加していません")
    await ctx.send("ユーザーが見つかりませんでした")


# 参加希望者を表示する
async def run_list(bot, ctx):
    if ctx.channel.id != cs.Recruit:
        return

    if len(cs.Joiner) >= 1:
        stc = [f"{i + 1}. {bot.get_user(cs.Joiner[i]).display_name}\n" for i in range(len(cs.Joiner))]
        await ctx.send(f"参加希望者リスト\n```{''.join(stc)}```", delete_after=20.0)
    else:
        await ctx.send("参加希望者はいません", delete_after=20.0)


# 参加希望者の抽選を行う
async def run_pickup(guild, ctx, num):
    if ctx.channel.id != cs.Recruit:
        return
    elif len(cs.Joiner) < num or num <= 0:
        return await ctx.send("正しい人数を入力してください")

    role_P = get_role(guild, cs.Participant)
    pick_num = sorted(random.sample(list(range(len(cs.Joiner))), num))  # 抽選を行う
    stc = [f"{i + 1}. {guild.get_member(cs.Joiner[pick_num[i]]).display_name}\n"
           for i in range(len(pick_num))]
    for i in pick_num:
        await guild.get_member(cs.Joiner[i]).add_roles(role_P)
    await ctx.send(f"参加者リスト 抽選結果\n```{''.join(stc)}```"
                   f"リストのユーザーにロール {role_P.mention} を付与しました\n配信用ボイスチャンネルに接続出来るようになります")
    cs.Joiner = []


class Stream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def c(self, ctx):
        if ctx.channel.id == cs.Recruit:
            await run_can(ctx)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def can(self, ctx):
        if ctx.channel.id == cs.Recruit:
            await run_can(ctx)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def d(self, ctx):
        if ctx.channel.id == cs.Recruit:
            await run_drop(ctx)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def drop(self, ctx):
        if ctx.channel.id == cs.Recruit:
            await run_drop(ctx)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def rm(self, ctx, name=None):
        await run_remove(self.bot.get_guild(cs.Server), ctx, name)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def remove(self, ctx, name=None):
        await run_remove(self.bot.get_guild(cs.Server), ctx, name)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def l(self, ctx):
        if ctx.channel.id == cs.Recruit:
            await run_list(self.bot, ctx)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def list(self, ctx):
        if ctx.channel.id == cs.Recruit:
            await run_list(self.bot, ctx)

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def pu(self, ctx, num=0):
        await run_pickup(self.bot.get_guild(cs.Server), ctx, num)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def pickup(self, ctx, num=0):
        await run_pickup(self.bot.get_guild(cs.Server), ctx, num)


def setup(bot):
    return bot.add_cog(Stream(bot))
