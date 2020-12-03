import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import constant as cs
from multi_func import get_role, role_check_admin, role_check_mode

Question = {}
Answer = {}


async def run_quizentry(bot, ctx, num):
    def ng_check(ctx_wait):
        return all([ctx.channel.id == ctx_wait.channel.id, not ctx_wait.author.bot,
                    ctx_wait.content != "", ctx_wait.content not in cs.Commands, role_check_admin(ctx_wait)])

    if num <= 0:
        return await ctx.send("問題数を入力してください")

    await ctx.send("クイズの問題を登録します(Backで1問前に戻る、Skipで次の問題へ、Cancelで中断)")
    i = 0
    while i < num:
        await ctx.send(f"**{i + 1}**/{num}問目の問題文を入力してください")
        reply = await bot.wait_for('message', check=ng_check)
        if reply.content.lower() == "back" and i >= 1:
            await ctx.send(f"{i}問目の登録に戻ります")
            i -= 1
        elif reply.content.lower() == "skip":
            await ctx.send(f"{i + 1}問目の登録をスキップします")
            i += 1
        elif reply.content.lower() == "cancel":
            await ctx.send("問題の登録を中断しました")
            return
        else:
            Question[f"Q{i + 1}"] = reply.content
            await ctx.send(f"{i + 1}問目の問題文を登録しました\n解答を入力してください")
            reply = await bot.wait_for('message', check=ng_check)
            if reply.content.lower() == "back" and i >= 1:
                await ctx.send(f"{i}問目の登録に戻ります")
                i -= 1
            elif reply.content.lower() == "cancel":
                await ctx.send("問題の登録を中断しました")
                return
            else:
                Answer[f"A{i + 1}"] = reply.content
                await ctx.send(f"{i + 1}問目の解答を登録しました")
                i += 1
    await ctx.send(f"全ての問題の登録が完了しました")


async def run_quizlineup(bot, ctx):
    if len(Question) != 0:
        await ctx.send("クイズの問題を表示します. よろしいですか？(Yes/No)")
        while True:
            reply = await bot.wait_for('message')
            if role_check_admin(reply):
                break
        if reply.content.lower() == "yes":
            await ctx.send("登録済み問題一覧")
            stc = [f"[Q{i + 1}] {Question[f'Q{i + 1}']}\n→ {Answer[f'A{i + 1}']}\n"
                   for i in range(len(Question))]
            await ctx.send(f"```{''.join(stc)}```")
        else:
            await ctx.send("キャンセルしました")
    else:
        await ctx.send("クイズは登録されていません")


async def run_quizreset(bot, ctx):
    global Question, Answer
    await ctx.send("クイズの問題を全消去します. よろしいですか？(Yes/No)")
    while True:
        reply = await bot.wait_for('message')
        if role_check_admin(reply):
            break
    if reply.content.lower() == "yes":
        Question, Answer = {}, {}
        await ctx.send("消去しました")
    else:
        await ctx.send("キャンセルしました")


async def run_quizstart(bot, guild, ctx, num):
    if num <= 0:
        await ctx.send("問題数を入力してください")
    elif not 1 <= num <= len(Question):
        await ctx.send("登録されている問題数に対して入力が間違っています")
        return

    result, point, mag = {}, [4, 2, 1], []
    mag = [3 if i + 1 == num else 1 if (i + 1) % 5 != 0 else 2 for i in range(num)]
    await ctx.send("クイズを開始します")
    for i in range(num):
        await asyncio.sleep(5)
        await ctx.send(f"問題**{i + 1}**/{num} **(1位 +{point[0] * mag[i]}点,  "
                       f"2位 +{point[1] * mag[i]}点,  3位 +{point[2] * mag[i]}点)** (制限時間1分)")
        await asyncio.sleep(3)
        await ctx.send(f"{Question[f'Q{i + 1}']}")
        j, flag, winner, start = 1, False, [], datetime.now()
        while 0 <= j <= 3:
            reply = await bot.wait_for('message')
            elap = (start - datetime.now()).seconds
            if reply.content == Answer[f'A{i + 1}'] and reply.channel.id == cs.Quiz_room:
                if reply.author.id not in winner:
                    winner.append(reply.author.id)
                    j, flag = j + 1, True
            elif (reply.content.lower() == "!skip" and role_check_admin(reply)) or elap > 60:
                await ctx.send(f"問題{i + 1}はスキップされました (正解 : {Answer[f'A{i + 1}']})")
                j, flag = -1, False
            elif reply.content.lower() == "!cancel" and role_check_admin(reply):
                await ctx.send(f"クイズを中断しました")
                return
        if flag:
            await ctx.send(f"正解者が出揃ったので問題{i + 1}を終了します (正解 : {Answer[f'A{i + 1}']})")
        if len(winner) != 0:
            stc = [f"{k + 1}位 : {bot.get_user(winner[k]).display_name} (+{point[k] * mag[i]}点)\n"
                   for k in range(len(winner))]
            await ctx.send(f"**```問題{i + 1} 結果\n{''.join(stc)}```**")
            for k in range(len(winner)):
                if winner[k] not in result:
                    result[winner[k]] = point[k] * mag[i]
                else:
                    new_pts = result[winner[k]] + point[k] * mag[i]
                    result[winner[k]] = new_pts

    all_user, all_result = list(result.keys()), sorted(list(result.values()), reverse=True)
    ranker = []
    embed = discord.Embed(color=0xFF0000)
    embed.set_author(name='Ranking', icon_url='https://i.imgur.com/F2oH0Bu.png')
    embed.set_thumbnail(url='https://i.imgur.com/jrl3EDv.png')
    i = 0
    while i < (len(all_user) if len(all_user) < 5 else 5):
        k = 0
        for j in range(len(all_user)):
            if result[all_user[j]] == all_result[i]:
                name = guild.get_member(all_user[j]).display_name
                embed.add_field(name=f"{i + 1}位", value=f"{name} ({all_result[i]}pts)")
                ranker.append(all_user[j])
                k += 1
        i += k
    role_A, role_W = get_role(guild, cs.Administrator), get_role(guild, cs.Winner)
    await ctx.send(embed=embed)
    await guild.get_member(ranker[0]).add_roles(role_W)
    await ctx.send(f"クイズを終了しました\n{role_W.mention} → {guild.get_member(ranker[0]).mention}")
    await ctx.send(f"{role_A.mention} `!out`で結果を {bot.get_channel(cs.Result).mention} に出力")
    while True:
        reply = await bot.wait_for('message', check=role_check_mode)
        if reply.content == "!out":
            await bot.get_channel(cs.Result).send(embed=embed)
            break


class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def qe(self, ctx, num=0):
        await run_quizentry(self.bot, ctx, num)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def quizentry(self, ctx, num=0):
        await run_quizentry(self.bot, ctx, num)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def ql(self, ctx):
        await run_quizlineup(self.bot, ctx)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def quizlineup(self, ctx):
        await run_quizlineup(self.bot, ctx)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def qr(self, ctx):
        await run_quizreset(self.bot, ctx)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def quizreset(self, ctx):
        await run_quizreset(self.bot, ctx)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def qs(self, ctx, num=0):
        await run_quizstart(self.bot, self.bot.get_guild(cs.Server), ctx, num)

    @commands.command()
    @commands.has_role(cs.Administrator)
    async def quizstart(self, ctx, num=0):
        await run_quizstart(self.bot, self.bot.get_guild(cs.Server), ctx, num)


def setup(bot):
    return bot.add_cog(Quiz(bot))
