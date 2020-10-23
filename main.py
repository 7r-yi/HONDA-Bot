import discord
from discord.ext import tasks
from datetime import datetime, timedelta
from pytz import timezone
import asyncio
import random
import os
from dotenv import load_dotenv
import json
import sys
import jaconv
import keep_alive
import constant
from zyanken import zyanken, zyanken_restore

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


@tasks.loop(minutes=10)
async def data_auto_save():
    with open('zyanken/zyanken_record.json', 'r') as f:
        before_zyanken_data = json.load(f)
    if constant.zyanken_data != before_zyanken_data:
        if constant.file_backup is not None:
            await constant.file_backup.delete()
        with open('zyanken/zyanken_record.json', 'w') as f:
            json.dump(constant.zyanken_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
        constant.file_backup = await client.get_channel(constant.Test_room).send(
            f"{time}\nData Auto Saved", file=discord.File('zyanken/zyanken_record.json'))


@client.event
async def on_ready():
    data_auto_save.start()
    boot_time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
    bot_msgs = await client.get_channel(constant.Test_room).history(limit=30).flatten()
    for msg in bot_msgs:
        if "Data input" in msg.content:
            time = datetime.strptime(msg.content.split("\n")[0], '%Y/%m/%d %H:%M:%S') - timedelta(hours=9)
            msgs = await client.get_channel(constant.Zyanken_room).history(limit=None, after=time) \
                .filter(lambda m: zyanken_restore.check_hand(m)).flatten()
            zyanken_restore.data_restore(msgs)
            await client.get_channel(constant.Test_room).send(
                f"{boot_time}\nBooted", file=discord.File('zyanken/zyanken_record.json'))
            break


@client.event
async def on_member_join(member):
    time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M')
    await client.get_channel(constant.Gate).send(f"{member.mention} が入室しました ({time})")


@client.event
async def on_member_remove(member):
    if str(member.id) in constant.zyanken_data:
        constant.zyanken_data.pop(member.id)
        if str(member.id) not in constant.rm_user_data:
            time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M')
            constant.rm_user_data[str(member.id)] = {str(member.id): time}


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

    if ctx.content.lower() in ["_sd", "_shutdown"] and role_check_admin(ctx):
        with open('zyanken/zyanken_record.json', 'w') as f:
            json.dump(constant.zyanken_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        await ctx.channel.send(file=discord.File('zyanken/zyanken_record.json'))
        await ctx.channel.send("Botをシャットダウンします")
        await client.logout()
        await sys.exit()

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
            await msg.delete()
            await ctx.delete()

    if not role_check_visit(ctx):  # 以下、@everyoneは実行不可
        return

    if ctx.content.count("\n") > 5 or len(ctx.content) > 200:
        if ctx.channel.id == constant.General and not ctx.author.bot:  # 長文を削除
            await ctx.delete()

    if ctx.channel.id == constant.Zyanken_room and not ctx.author.bot:
        hands = ["グー", "チョキ", "パー"]
        for hand in hands:
            if hand in jaconv.hira2kata(jaconv.h2z(ctx.content)):  # グー,チョキ,パーの順に文字が含まれているか検索
                img, hand, msg, emoji1, emoji2 = zyanken.honda_to_zyanken(hand, ctx.author.id)
                await ctx.add_reaction(emoji1)
                await ctx.add_reaction(emoji2)
                if ctx.author.id not in constant.No_reply:
                    msg = await ctx.channel.send(f"{ctx.author.mention} {hand}\n**{msg}**", file=discord.File(img))
                    await asyncio.sleep(5)
                    await msg.delete()
                return

    if ctx.content.lower() in ["_nr", "_noreply"]:
        if ctx.author.id in constant.No_reply.append:
            constant.No_reply.append(ctx.author.id)
            await ctx.channel.send(f"{ctx.author.mention} 返信を無効にしました")
        else:
            await ctx.channel.send(f"{ctx.author.mention} 既に返信が無効になっています")

    if ctx.content.lower() in ["_cnr", "_cancelnoreply"]:
        if ctx.author.id in constant.No_reply.append:
            constant.No_reply.pop(ctx.author.id)
            await ctx.channel.send(f"{ctx.author.mention} 返信を有効にしました")
        else:
            await ctx.channel.send(f"{ctx.author.mention} 既に返信は有効になっています")

    if ctx.content.split(" ")[0].lower() in ["_st", "_stats"]:
        if ctx.channel.id != constant.Zyanken_room and ctx.channel.id != constant.Test_room:
            return
        name = ctx.content[ctx.content.find(" ") + 1:]  # プレイヤーのじゃんけん戦績を表示
        if " " not in ctx.content.strip():
            guild = client.get_guild(constant.Server)
            name = guild.get_member(ctx.author.id).display_name
        role = discord.utils.get(ctx.guild.roles, id=constant.Visitor)
        data, user = None, None
        for member in role.members:
            if name.lower() == member.display_name.lower():
                if str(member.id) in constant.zyanken_data:
                    data = zyanken.stats_output(member.id)
                    user = member.display_name
                else:
                    await ctx.channel.send("データが記録されていません")
                    return
        if name == "ケイスケホンダ" and data is None:
            data = zyanken.stats_output(constant.Honda)
            user = name
        elif data is None:
            await ctx.channel.send("データが見つかりませんでした")
            return
        embed = discord.Embed(title=user, color=0x7CFC00)
        embed.set_author(name='Stats', icon_url='https://i.imgur.com/dUXKlUj.png')
        embed.set_thumbnail(url=data[6])
        embed.add_field(name="勝率", value=f"{data[2]:.02f}% ({data[0] + data[1]}戦 {data[0]}勝{data[1]}敗)", inline=False)
        embed.add_field(name="グー勝ち", value=f"{data[3][0]}回")
        embed.add_field(name="チョキ勝ち", value=f"{data[3][1]}回")
        embed.add_field(name="パー勝ち", value=f"{data[3][2]}回")
        embed.add_field(name="グー負け", value=f"{data[4][0]}回")
        embed.add_field(name="チョキ負け", value=f"{data[4][1]}回")
        embed.add_field(name="パー負け", value=f"{data[4][2]}回")
        embed.add_field(name="連勝数", value=f"現在{data[5][1]}連勝中 (最大{data[5][2]}連勝)")
        await ctx.channel.send(embed=embed)

    if ctx.content.split(" ")[0].lower() in ["_rk", "_ranking"]:
        if ctx.channel.id != constant.Zyanken_room and ctx.channel.id != constant.Test_room:
            return
        type = ctx.content[ctx.content.find(" ") + 1:].lower()  # プレイヤーのじゃんけん戦績を表示
        if type in ["wins", "winsall", "winskeep", "losesall"]:
            guild = client.get_guild(constant.Server)
            title, stc, best, worst = zyanken.ranking_output(type, guild)
            await ctx.channel.send(f"じゃんけん戦績ランキング({title})")
            cnt = len(stc) // 1900
            if cnt >= 1:  # 文字数が多い場合は分割して送信
                start = 0
                for i in range(cnt + 1):
                    j = 0
                    while True:
                        if stc[start + 1900 - j] == "\n":  # 1900文字毎を目安、改行で区切る
                            await ctx.channel.send(f"```{stc[start:(start + 1900 - j)]}```")
                            start = start + 1900 - j
                            break
                        j -= 1
                    if i == cnt - 1:
                        await ctx.channel.send(f"```{stc[start:]}```")
                        break
            else:
                await ctx.channel.send(f"```{stc}```")
            role1 = discord.utils.get(ctx.guild.roles, id=constant.Winner)
            role2 = discord.utils.get(ctx.guild.roles, id=constant.Loser)
            if type in ["wins", "winskeep"]:
                if type == "wins":
                    before_check, same_check = constant.Former_winner_wins, constant.Former_winner_keep
                    constant.Former_winner_wins = best
                else:  # type == "winskeep":
                    before_check, same_check = constant.Former_winner_keep, constant.Former_winner_wins
                    constant.Former_winner_keep = best
                if before_check is not None and before_check != same_check:
                    await guild.get_member(before_check).remove_roles(role1)
                if best != constant.Former_loser_all and best != constant.Former_loser_loses:
                    await guild.get_member(best).add_roles(role1)
            elif type == "winsall":
                if constant.Former_loser_all is not None:
                    await guild.get_member(constant.Former_loser_all).remove_roles(role2)
                await guild.get_member(worst).add_roles(role2)
                constant.Former_loser_all = worst
            else:  # type == "losesall"
                if constant.Former_loser_all is not None:
                    await guild.get_member(constant.Former_loser_loses).remove_roles(role2)
                await guild.get_member(worst).add_roles(role2)
                constant.Former_loser_loses = worst
        else:
            await ctx.channel.send("Typeを入力してください\n>>> **_RanKing Type**\nType = Wins / WinsKeep / WinsAll / LosesAll")

    if ctx.content in ["_ss", "_statssave"] and role_check_mode(ctx):
        with open('zyanken/zyanken_record.json', 'w') as f:
            json.dump(constant.zyanken_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        await ctx.channel.send(file=discord.File('zyanken/zyanken_record.json'))
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
        await ctx.channel.send(f"全戦績データを出力＆セーブしました ({time})")

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

    if ctx.content.split(" ")[0].lower() in ["_rs", "_reset"] and role_check_mode(ctx):  # ロールをリセットする
        role_name = ctx.content[ctx.content.find(" ") + 1:].lower()
        if role_name == "participant":
            id = constant.Participant
            constant.Joiner = []
        elif role_name == "winner":
            id = constant.Winner
        else:
            await ctx.channel.send("RoleNameを入力してください\n>>> **_ReSet RoleName**\nRoleName = Participant / Winner")
            return
        role = discord.utils.get(ctx.guild.roles, id=id)
        for member in role.members:
            if member.id != constant.Shichi:
                await member.remove_roles(role)
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
                if reply.content == constant.Answer[f'A{i + 1}'] and reply.channel.id == constant.Quiz_room:
                    if reply.author.id not in winner:
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
