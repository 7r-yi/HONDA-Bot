import discord
from datetime import datetime
from pytz import timezone
import asyncio
import random
import os
from dotenv import load_dotenv
import keep_alive
import constant
import zyanken

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


@client.event
async def on_member_join(member):
    time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M')
    await client.get_channel(constant.Gate).send(f"{member.mention} が入室しました ({time})")


@client.event
async def on_message(ctx):
    def bot_check(ctx_wait):
        return not ctx_wait.author.bot

    def role_check_admin(ctx_role):
        return 'Administrator' in [roles.name for roles in ctx_role.author.roles]

    def role_check_mode(ctx_role):
        roles = [roles.name for roles in ctx_role.author.roles]
        return any(['Administrator' in roles, 'Moderator' in roles])

    def role_check_visit(ctx_role):
        roles = [roles.name for roles in ctx_role.author.roles]
        return any(['Administrator' in roles, 'Moderator' in roles, 'Visitor' in roles])

    if ctx.channel.id == constant.Gate and not ctx.author.bot:  # Gateでの入力チェック
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo'))
        password = f"_join {time.strftime('%Y/%m/%d')}"
        if ctx.content == password:
            await ctx.delete()
            role = discord.utils.get(ctx.guild.roles, id=constant.Visitor)
            await ctx.author.add_roles(role)
            await ctx.channel.send(f"{ctx.author.mention} 参加しました ({time.strftime('%Y/%m/%d %H:%M')})")
        else:
            msg = await ctx.channel.send(f'{ctx.author.mention} コマンドが違います')
            await asyncio.sleep(5)
            await ctx.delete()
            await msg.delete()

    if not role_check_visit(ctx):  # 以下、@everyoneは実行不可
        return

    if ctx.content in ["グー", "チョキ", "パー"] and ctx.channel.id == constant.Zyanken_room and not ctx.author.bot:
        img, hand, msg, emoji1, emoji2 = zyanken.honda_to_zyanken(ctx.content, ctx.author.id)
        await ctx.add_reaction(emoji1)
        await ctx.add_reaction(emoji2)
        msg1 = await ctx.channel.send(f"{ctx.author.mention} {hand}", file=discord.File(img))
        msg2 = await ctx.channel.send(f"**{msg}**")
        await asyncio.sleep(10)
        await msg1.delete()
        await msg2.delete()

    if ctx.content.split(" ")[0].lower() in ["_st", "_stats"]:  # プレイヤーのじゃんけん戦績を表示
        name = ctx.content[ctx.content.find(" ") + 1:]
        if " " not in ctx.content.strip():
            guild = client.get_guild(constant.Server)
            name = guild.get_member(ctx.author.id).display_name
        role = discord.utils.get(ctx.guild.roles, id=constant.Visitor)
        for member in role.members:
            if name.lower() == member.display_name.lower():
                try:
                    data = zyanken.stats_output(member.id)
                except KeyError:
                    await ctx.channel.send("データが見つかりませんでした")
                    return
                embed = discord.Embed(title=member.display_name, color=0xFF8000)
                embed.set_author(name='Stats', icon_url='https://i.imgur.com/dUXKlUj.png')
                embed.set_thumbnail(url=data[5])
                embed.add_field(name="勝率", value=f"{data[2]}% ({data[0] + data[1]}戦 {data[0]}勝{data[1]}敗)",
                                inline=False)
                embed.add_field(name="グー勝ち", value=f"{data[3][0]}回")
                embed.add_field(name="チョキ勝ち", value=f"{data[3][1]}回")
                embed.add_field(name="パー勝ち", value=f"{data[3][2]}回")
                embed.add_field(name="グー負け", value=f"{data[4][0]}回")
                embed.add_field(name="チョキ負け", value=f"{data[4][1]}回")
                embed.add_field(name="パー負け", value=f"{data[4][2]}回")
                await ctx.channel.send(embed=embed)
                break

    if ctx.content.split(" ")[0].lower() in ["_rk", "_ranking"]:  # プレイヤーのじゃんけん戦績を表示
        if ctx.content[ctx.content.find(" ") + 1:].lower() in ["wins", "rate"]:
            type = ctx.content[ctx.content.find(" ") + 1:].lower()
        else:
            await ctx.channel.send("Typeを入力してください\n>>> **_ranking X**\nX = Wins or Rate")
            return
        users_data, sort_data = zyanken.ranking_output(type)
        guild = client.get_guild(constant.Server)
        stc = "```"
        if type == "wins":
            title = "勝利数基準"
            for i in range(len(users_data)):
                if sort_data[0][1] == users_data[i][0]:
                    stc += f"{i + 1}位 : {guild.get_member(users_data[i][0]).display_name} " \
                           f"({users_data[i][1]}勝{users_data[i][2]}負, 勝率{round(users_data[i][4], 2)}%\n"
                    break
        else:  # type == "rate"
            title = "勝率基準"
            for i in range(len(users_data)):
                if sort_data[0][1] == users_data[i][0]:
                    stc += f"{i + 1}位 : {guild.get_member(users_data[i][0]).display_name} " \
                           f"({round(users_data[i][4], 2)}%, {users_data[i][1]}勝{users_data[i][2]}負)\n"
                    break
        stc += "```"
        await ctx.channel.send(f"じゃんけん戦績ランキング({title}){stc}")

    if ctx.content in ["_so", "_statsoutput"] and role_check_admin(ctx):
        await ctx.channel.send(file=discord.File('zyanken_record.json'))
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
        await ctx.channel.send(f"出力しました ({time})")

    if ctx.channel.id == constant.Recruit and ctx.content.lower() in ["_c", "_can"]:  # 参加希望を出す
        if ctx.author.id not in constant.Joiner:
            constant.Joiner.append(ctx.author.id)
            msg = await ctx.channel.send(f'{ctx.author.mention} 参加希望者リストに追加しました')
        else:
            msg = await ctx.channel.send(f'{ctx.author.mention} すでに参加希望が出されています')
        await asyncio.sleep(5)
        await msg.delete()

    if ctx.channel.id == constant.Recruit and ctx.content.lower() in ["_d", "_drop"]:  # 参加希望を取り消す
        if ctx.author.id in constant.Joiner:
            constant.Joiner.remove(ctx.author.id)
            msg = await ctx.channel.send(f'{ctx.author.mention} 参加希望を取り消しました')
        else:
            msg = await ctx.channel.send(f'{ctx.author.mention} 参加希望が出されていません')
        await asyncio.sleep(5)
        await msg.delete()

    if ctx.channel.id == constant.Recruit and ctx.content.lower() in ["_l", "_list"]:  # 参加希望者を表示する
        if len(constant.Joiner) >= 1:
            stc = "参加希望者リスト\n```"
            for i in range(len(constant.Joiner)):
                stc += f"{i + 1}. {client.get_user(constant.Joiner[i]).display_name}\n"
            stc += "```"
        else:
            stc = "参加希望者はいません"
        msg = await ctx.channel.send(stc)
        await asyncio.sleep(20)
        await msg.delete()

    if ctx.content.split(" ")[0].lower() in ["_pu", "_pickup"] and role_check_mode(ctx):  # 参加希望者の抽選を行う
        try:
            num = int(ctx.content[ctx.content.find(" ") + 1:])
            num_list = list(range(len(constant.Joiner)))
            pick_num = sorted(random.sample(num_list, num))
            stc = "参加者リスト 抽選結果\n```"
            for i in pick_num:
                stc += f"{i + 1}. {client.get_user(constant.Joiner[i]).display_name}\n"
            stc += "```"
            guild = client.get_guild(constant.Server)
            role = discord.utils.get(ctx.guild.roles, id=constant.Participant)
            for i in pick_num:
                await guild.get_member(constant.Joiner[i]).add_roles(role)
            await ctx.channel.send(f"{stc}リストのユーザーにロール {role.mention} を付与しました\n"
                                   f"配信用ボイスチャンネルに接続出来るようになります")
            constant.Joiner = []
        except ValueError:
            await ctx.channel.send("入力エラー")

    if ctx.content.lower() in ["_r", "_reset"] and role_check_mode(ctx):
        role = discord.utils.get(ctx.guild.roles, id=constant.Participant)
        for member in role.members:
            if member.id != constant.Shichi:
                await member.remove_roles(role)  # ロールParticipantをリセットする
        constant.Joiner = []
        await ctx.channel.send(f"ロール {role.mention} をリセットしました")

    if ctx.content.split(" ")[0].lower() in ["_qe", "_quizentry"] and role_check_admin(ctx):
        try:
            num = int(ctx.content[ctx.content.find(" ") + 1:])
        except:
            await ctx.channel.send("入力エラー")
            return
        await ctx.channel.send("クイズの問題を登録します(Backで1問前に戻る、Skipで次の問題へ、Cancelで中断)")
        i = 0
        while i < num:
            await ctx.channel.send(f"**{i + 1}**/{num}問目の問題文を入力してください")
            while True:
                reply = await client.wait_for('message', check=bot_check)
                if role_check_admin(reply):
                    break
            if reply.content.lower() == "back" and i >= 1:
                await ctx.channel.send(f"{i}問目の登録に戻ります")
                i -= 1
            elif reply.content.lower() == "skip":
                await ctx.channel.send(f"{i + 1}問目の登録をスキップします")
                i += 1
            elif reply.content.lower() == "cancel":
                await ctx.channel.send("問題の登録を中断しました")
                return
            else:
                constant.Question[f"Q{i + 1}"] = reply.content
                await ctx.channel.send(f"{i + 1}問目の問題文を登録しました\n解答を入力してください")
                while True:
                    reply = await client.wait_for('message', check=bot_check)
                    if role_check_admin(reply):
                        break
                if reply.content.lower() == "back" and i >= 1:
                    await ctx.channel.send(f"{i}問目の登録に戻ります")
                    i -= 1
                elif reply.content.lower() == "cancel":
                    await ctx.channel.send("問題の登録を中断しました")
                    return
                else:
                    constant.Answer[f"A{i + 1}"] = reply.content
                    await ctx.channel.send(f"{i + 1}問目の解答を登録しました")
                    i += 1
        await ctx.channel.send(f"全ての問題の登録が完了しました")

    if ctx.content.lower() in ["_qr", "_quizreset"] and role_check_admin(ctx):
        await ctx.channel.send("クイズの問題を全消去します. よろしいですか？(Yes/No)")
        while True:
            reply = await client.wait_for('message', check=bot_check)
            if role_check_admin(reply):
                break
        if reply.content.lower() == "yes":
            constant.Question = {}
            constant.Answer = {}
            await ctx.channel.send("消去しました")
        else:
            await ctx.channel.send("キャンセルしました")
            return

    if ctx.content.split(" ")[0].lower() in ["_qs", "_quizstart"] and role_check_admin(ctx):
        try:
            num = int(ctx.content[ctx.content.find(" ") + 1:])
        except:
            await ctx.channel.send("入力エラー")
            return
        result, point, mag = {}, [4, 2, 1], []
        for i in range(num):
            if i + 1 == num:
                mag.append(3)
            elif (i + 1) % 5 != 0:
                mag.append(1)
            else:
                mag.append(2)
        await ctx.channel.send("クイズを開始します")

        for i in range(num):
            await asyncio.sleep(5)
            await ctx.channel.send(f"問題**{i + 1}**/{num} **(1位 +{point[0] * mag[i]}点,  "
                                   f"2位 +{point[1] * mag[i]}点,  3位 +{point[2] * mag[i]}点)**")
            await asyncio.sleep(3)
            await ctx.channel.send(f"{constant.Question[f'Q{i + 1}']}")
            j, flag, winner = 1, False, []
            while 0 <= j <= 3:
                reply = await client.wait_for('message', check=bot_check)
                if reply.content == constant.Answer[f'A{i + 1}'] and reply.author.id not in winner:
                    winner.append(reply.author.id)
                    j, flag = j + 1, True
                elif reply.content.lower() == "skip" and role_check_admin(reply):
                    await ctx.channel.send(f"問題{i + 1}はスキップされました (正解 : {constant.Answer[f'A{i + 1}']})")
                    j = -1
                elif reply.content.lower() == "cancel" and role_check_admin(reply):
                    await ctx.channel.send(f"クイズを中断しました")
                    return
            if flag:
                await ctx.channel.send(f"正解者が出揃ったので問題{i + 1}を終了します (正解 : {constant.Answer[f'A{i + 1}']})")
            if len(winner) != 0:
                stc = f"```問題{i + 1} 結果\n"
                for k in range(len(winner)):
                    stc += f"{k + 1}位 : {client.get_user(winner[k]).display_name} (+{point[k] * mag[i]}点)\n"
                stc += "```"
                await ctx.channel.send(stc)
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
        i, n = 0, 5
        if len(all_user) < 5:
            n = len(all_user)
        while i < n:
            k = 0
            for j in range(len(all_user)):
                if result[all_user[j]] == all_result[i]:
                    name = client.get_user(all_user[j]).display_name
                    embed.add_field(name=f"{i + 1}位", value=f"{name} ({all_result[i]}pts)")
                    ranker.append(all_user[j])
                    k += 1
            i += k
        await ctx.channel.send(embed=embed)
        guild = client.get_guild(constant.Server)
        role = discord.utils.get(ctx.guild.roles, id=constant.Winner)
        await guild.get_member(ranker[0]).add_roles(role)
        await ctx.channel.send(f"クイズを終了しました\n{role.mention} → {guild.get_member(ranker[0]).mention}")


keep_alive.keep_alive()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
client.run(os.environ.get('TOKEN'))
