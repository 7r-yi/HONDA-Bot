import discord
from discord.ext import tasks
from datetime import datetime
from pytz import timezone
import asyncio
import random
import re
import os
from dotenv import load_dotenv
import json
import sys
import jaconv
import constant
from zyanken import zyanken

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


@tasks.loop(minutes=1)
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
    for type in ["point", "pointall"]:
        _, _, _, worst = zyanken.ranking_output(type, client.get_guild(constant.Server))
        if type == "point":
            constant.Former_loser_point = worst
        else:  # type == "pointall"
            constant.Former_loser_pointall = worst


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
    def role_check_admin(ctx_role):
        return 'Administrator' in [roles.name for roles in ctx_role.author.roles]

    def role_check_mode(ctx_role):
        roles = [roles.name for roles in ctx_role.author.roles]
        return any(['Administrator' in roles, 'Moderator' in roles])

    def role_check_visit(ctx_role):
        roles = [roles.name for roles in ctx_role.author.roles]
        return any(['Administrator' in roles, 'Moderator' in roles, 'Visitor' in roles])

    if ctx.author.bot:  # Botのメッセージには反応させない
        return

    guild = client.get_guild(constant.Server)
    role_A = discord.utils.get(ctx.guild.roles, id=constant.Administrator)
    role_W = discord.utils.get(ctx.guild.roles, id=constant.Winner)
    role_L = discord.utils.get(ctx.guild.roles, id=constant.Loser)
    role_P = discord.utils.get(ctx.guild.roles, id=constant.Participant)
    role_V = discord.utils.get(ctx.guild.roles, id=constant.Visitor)
    role_C = discord.utils.get(ctx.guild.roles, id=constant.Challenger)

    if ctx.content.lower() in ["_sd", "_shutdown"] and role_check_admin(ctx):
        with open('zyanken/zyanken_record.json', 'w') as f:
            json.dump(constant.zyanken_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        await ctx.channel.send(file=discord.File('zyanken/zyanken_record.json'))
        await ctx.channel.send("Botをシャットダウンします")
        await client.logout()
        await sys.exit()

    if ctx.channel.id == constant.Gate:  # Gateでの入力チェック
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo'))
        password = f"_join {time.strftime('%Y/%m/%d')}"
        if ctx.content == password:
            await ctx.delete()
            await ctx.author.add_roles(role_V)
            await ctx.channel.send(f"{ctx.author.mention} 参加しました ({time.strftime('%Y/%m/%d %H:%M')})")
        else:
            await ctx.delete(delay=5.0)
            await ctx.channel.send(f'{ctx.author.mention} コマンドが違います', delete_after=5.0)

    if not role_check_visit(ctx):  # 以下、@everyoneは実行不可
        return

    if ctx.content.count("\n") > 7 or len(ctx.content) > 400:
        if ctx.channel.id == constant.General and not role_check_mode(ctx):  # 長文を削除
            await ctx.delete()
            await ctx.channel.send(f"{ctx.author.mention} 改行/文字数が多いため削除されました", delete_after=3.0)

    if ctx.channel.id == constant.Zyanken_room or ctx.channel.id == constant.Test_room:
        for hand in ["グー", "チョキ", "パー"]:
            if hand in jaconv.hira2kata(jaconv.h2z(ctx.content)):  # グー,チョキ,パーの順に文字が含まれているか検索
                img, hand, msg, emoji1, emoji2 = zyanken.honda_to_zyanken(hand, ctx.author.id)
                if ctx.author.id not in constant.No_reply:
                    await ctx.add_reaction(emoji1)
                    await ctx.add_reaction(emoji2)
                    await ctx.channel.send(f"{ctx.author.mention} {hand}\n**{msg}**",
                                           file=discord.File(img), delete_after=5.0)
                if 'Challenger' not in [roles.name for roles in ctx.author.roles]:
                    await guild.get_member(ctx.author.id).add_roles(role_C)
                break

    if ctx.content.split()[0].lower() in ["_nr", "_noreply"] and ctx.channel.id == constant.Zyanken_room:
        name = ctx.content[ctx.content.find(" ") + 1:].strip()  # プレイヤーのじゃんけん戦績を表示
        if " " not in ctx.content.strip():
            name = guild.get_member(ctx.author.id).display_name
        for member in role_V.members:
            if name.lower() == member.display_name.lower():
                if member.id not in constant.No_reply:
                    constant.No_reply.append(member.id)
                    await ctx.channel.send(f"{guild.get_member(member.id).mention} 返信を無効にしました")
                else:
                    await ctx.channel.send(f"{ctx.author.mention} 既に返信が無効になっています")
                return
        await ctx.channel.send(f"{ctx.author.mention} ユーザーが見つかりませんでした")

    if ctx.content.split()[0].lower() in ["_nrc", "_noreplycancel"] and ctx.channel.id == constant.Zyanken_room:
        name = ctx.content[ctx.content.find(" ") + 1:].strip()  # プレイヤーのじゃんけん戦績を表示
        if " " not in ctx.content.strip():
            name = guild.get_member(ctx.author.id).display_name
        for member in role_V.members:
            if name.lower() == member.display_name.lower():
                if member.id in constant.No_reply:
                    constant.No_reply.remove(member.id)
                    await ctx.channel.send(f"{guild.get_member(member.id).mention} 返信を有効にしました")
                else:
                    await ctx.channel.send(f"{ctx.author.mention} 既に返信は有効になっています")
                return
        await ctx.channel.send(f"{ctx.author.mention} ユーザーが見つかりませんでした")

    if ctx.content.split()[0].lower() in ["_st", "_stats"]:  # プレイヤーのじゃんけん戦績を表示
        if ctx.channel.id != constant.Zyanken_room and not role_check_mode(ctx):  # じゃんけん会場のみ反応(モデレーター以外)
            return
        name = ctx.content[ctx.content.find(" ") + 1:].strip()
        if " " not in ctx.content.strip():
            name = guild.get_member(ctx.author.id).display_name
        data, user, id = None, None, None
        for member in role_V.members:
            if name.lower() == member.display_name.lower():
                if str(member.id) in constant.zyanken_data:
                    data = zyanken.stats_output(member.id)
                    user, id = member.display_name, member.id
                else:
                    await ctx.channel.send(f"{ctx.author.mention} データが記録されていません")
                    return
        if name == "ケイスケホンダ" and data is None:
            data = zyanken.stats_output(constant.Honda)
            user, id = name, constant.Honda
        elif data is None:
            await ctx.channel.send(f"{ctx.author.mention} データが見つかりませんでした")
            return
        embed = discord.Embed(title=user, color=0x9932CC)
        embed.set_author(name='Stats', icon_url=client.get_user(id).avatar_url)
        embed.set_thumbnail(url=data[7])
        embed.add_field(name="勝率", value=f"{data[2]:.02f}% ({data[0] + data[1]}戦 {data[0]}勝{data[1]}敗)", inline=False)
        embed.add_field(name="グー勝ち", value=f"{data[3][0]}回")
        embed.add_field(name="チョキ勝ち", value=f"{data[3][1]}回")
        embed.add_field(name="パー勝ち", value=f"{data[3][2]}回")
        embed.add_field(name="グー負け", value=f"{data[4][0]}回")
        embed.add_field(name="チョキ負け", value=f"{data[4][1]}回")
        embed.add_field(name="パー負け", value=f"{data[4][2]}回")
        embed.add_field(name="連勝数", value=f"現在{data[5][0]}連勝中 (最大{data[5][1]}連勝)")
        embed.add_field(name="得点", value=f"{data[6]}点")
        await ctx.channel.send(embed=embed)

    if ctx.content.split()[0].lower() in ["_rk", "_ranking"]:  # ランキングを表示
        if ctx.channel.id != constant.Zyanken_room and not role_check_mode(ctx):  # じゃんけん会場のみ反応(モデレーター以外)
            return
        if len(ctx.content.split()) == 1:
            type = "point"
        else:
            type = ctx.content.replace(ctx.content.split()[0], "").strip()
        if type.split()[0].lower() in ["p", "point", "pa", "pointall"]:
            type = "point" if type.split()[0].lower() in ["p", "point"] else "pointall"
            try:
                num = int(re.sub(r'[^0-9]', "", ctx.content))
                if type == "point" and num >= 6:
                    num += 1
            except ValueError:
                num = 999
        else:
            await ctx.channel.send(f"{ctx.author.mention} 入力形式が間違っています\n"
                                   ">>> **_RanKing Type N**\nType = Point / PointAll (未入力の場合 : Point)\n"
                                   "N : 上位N名を表示 (未入力/範囲外の場合 : 対象者全員)")
            return
        title, stc, best, worst = zyanken.ranking_output(type, guild)
        if len(stc) == 0:
            await ctx.channel.send("現在、対象者はいません")
            return
        await ctx.channel.send(f"じゃんけん戦績ランキング【{title}】")
        stc_split, i = stc.split("\n"), 0
        stc_split.append("")
        send_times = num if 1 <= num < len(stc_split) else len(stc_split) - 1
        while i < send_times:  # 2000文字以下に分割して送信
            msg, length = "", len(stc_split[i]) + 1
            while all([length < 1990, i < send_times]):
                msg += stc_split[i] + "\n"
                length += len(stc_split[i + 1]) + 1
                i += 1
            await ctx.channel.send(f"```{msg}```")
        if type == "point":
            for member in role_W.members:
                await member.remove_roles(role_W)
            for user in best:
                await guild.get_member(user).add_roles(role_W)
            if constant.Former_loser_point != worst:
                await guild.get_member(worst).add_roles(role_L)
                await guild.get_member(constant.Former_loser_point).remove_roles(role_L)
            constant.Former_loser_point = worst
        else:  # type == "pointall"
            if constant.Former_loser_pointall != worst:
                await guild.get_member(worst).add_roles(role_L)
                await guild.get_member(constant.Former_loser_pointall).remove_roles(role_L)
            constant.Former_loser_pointall = worst

    if ctx.content in ["_ss", "_statssave"] and role_check_mode(ctx):
        with open('zyanken/zyanken_record.json', 'w') as f:
            json.dump(constant.zyanken_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        await ctx.channel.send(file=discord.File('zyanken/zyanken_record.json'))
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
        await ctx.channel.send(f"全戦績データを出力＆セーブしました ({time})")

    if ctx.content.lower() in ["_c", "_can"]:  # 参加希望を出す
        if ctx.author.id not in constant.Joiner:
            constant.Joiner.append(ctx.author.id)
            await ctx.channel.send(f'{ctx.author.mention} 参加希望者リストに追加しました', delete_after=5.0)
        else:
            await ctx.channel.send(f'{ctx.author.mention} すでに参加希望が出されています', delete_after=5.0)

    if ctx.channel.id == constant.Recruit and ctx.content.lower() in ["_d", "_drop"]:  # 参加希望を取り消す
        if ctx.author.id in constant.Joiner:
            constant.Joiner.remove(ctx.author.id)
            await ctx.channel.send(f'{ctx.author.mention} 参加希望を取り消しました', delete_after=5.0)
        else:
            await ctx.channel.send(f'{ctx.author.mention} 参加希望が出されていません', delete_after=5.0)

    if ctx.channel.id == constant.Recruit and ctx.content.lower() in ["_l", "_list"]:  # 参加希望者を表示する
        if len(constant.Joiner) >= 1:
            stc = "参加希望者リスト\n```"
            for i in range(len(constant.Joiner)):
                stc += f"{i + 1}. {client.get_user(constant.Joiner[i]).display_name}\n"
            stc += "```"
        else:
            stc = "参加希望者はいません"
        await ctx.channel.send(stc, delete_after=20.0)

    if ctx.content.split()[0].lower() in ["_pu", "_pickup"] and role_check_mode(ctx):  # 参加希望者の抽選を行う
        try:
            lottery = []
            for i in range(len(constant.Joiner)):  # 当選確率 Star 10倍, Challenger 5倍
                roles = [roles.name for roles in guild.get_member(constant.Joiner[i]).roles]
                adv = 10 if 'Star' in roles else 5 if 'Challenger' in roles else 1
                for _ in range(adv):
                    lottery.append(constant.Joiner[i])
            num = int(ctx.content[ctx.content.find(" ") + 1:].strip())
            pick_num = sorted(random.sample(list(range(len(lottery))), num))  # 抽選を行う
            stc = "参加者リスト 抽選結果\n```"
            for i in range(len(pick_num)):
                stc += f"{i + 1}. {guild.get_member(lottery[pick_num[i]]).display_name}\n"
            stc += "```"
            for i in pick_num:
                await guild.get_member(lottery[i]).add_roles(role_P)
            await ctx.channel.send(f"{stc}リストのユーザーにロール {role_P.mention} を付与しました\n"
                                   f"配信用ボイスチャンネルに接続出来るようになります")
            constant.Joiner = []
        except ValueError:
            await ctx.channel.send("入力エラー")

    if ctx.content.split()[0].lower() in ["_rs", "_reset"] and role_check_mode(ctx):  # ロールをリセットする
        role_name = ctx.content[ctx.content.find(" ") + 1:].strip().lower()
        if role_name in ["participant", "p"]:
            id = constant.Participant
            constant.Joiner = []
        elif role_name in ["winner", "w"]:
            id = constant.Winner
        elif role_name in ["loser", "l"]:
            id = constant.Loser
        elif role_name in ["challenger", "c"]:
            id = constant.Challenger
        else:
            await ctx.channel.send(f"{ctx.author.mention} RoleNameを入力してください\n"
                                   ">>> **_ReSet RoleName**\nRoleName = Participant / Winner / Loser / Challenger")
            return
        role = discord.utils.get(ctx.guild.roles, id=id)
        for member in role.members:
            await member.remove_roles(role)
        await ctx.channel.send(f"ロール {role_name.capitalize()} をリセットしました")

    if ctx.content.split()[0].lower() in ["_qe", "_quizentry"] and role_check_admin(ctx):
        try:
            num = int(ctx.content[ctx.content.find(" ") + 1:].strip())
        except:
            await ctx.channel.send("入力エラー")
            return
        await ctx.channel.send("クイズの問題を登録します(Backで1問前に戻る、Skipで次の問題へ、Cancelで中断)")
        i = 0
        while i < num:
            await ctx.channel.send(f"**{i + 1}**/{num}問目の問題文を入力してください")
            while True:
                reply = await client.wait_for('message')
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
                    reply = await client.wait_for('message')
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

    if ctx.content.lower() in ["_ql", "_quizlineup"] and role_check_admin(ctx):
        if len(constant.Question) != 0:
            await ctx.channel.send("クイズの問題を表示します. よろしいですか？(Yes/No)")
            while True:
                reply = await client.wait_for('message')
                if role_check_admin(reply):
                    break
            if reply.content.lower() == "yes":
                await ctx.channel.send("登録済み問題一覧")
                stc = ""
                for i in range(len(constant.Question)):
                    stc += f"[Q{i + 1}] {constant.Question[f'Q{i + 1}']}\n"
                    stc += f"→ {constant.Answer[f'A{i + 1}']}\n"
                await ctx.channel.send(f"```{stc}```")
            else:
                await ctx.channel.send("キャンセルしました")
        else:
            await ctx.channel.send("クイズは登録されていません")

    if ctx.content.lower() in ["_qr", "_quizreset"] and role_check_admin(ctx):
        await ctx.channel.send("クイズの問題を全消去します. よろしいですか？(Yes/No)")
        while True:
            reply = await client.wait_for('message')
            if role_check_admin(reply):
                break
        if reply.content.lower() == "yes":
            constant.Question, constant.Answer = {}, {}
            await ctx.channel.send("消去しました")
        else:
            await ctx.channel.send("キャンセルしました")

    if ctx.content.split()[0].lower() in ["_qs", "_quizstart"] and role_check_admin(ctx):
        try:
            num = int(ctx.content[ctx.content.find(" ") + 1:].strip())
            if not 1 <= num <= len(constant.Question):
                await ctx.channel.send("登録されている問題数に対して入力が間違っています")
                return
        except:
            await ctx.channel.send("入力エラー")
            return

        result, point, mag = {}, [4, 2, 1], []
        mag = [3 if i + 1 == num else 1 if (i + 1) % 5 != 0 else 2 for i in range(num)]
        await ctx.channel.send("クイズを開始します")
        for i in range(num):
            await asyncio.sleep(5)
            await ctx.channel.send(f"問題**{i + 1}**/{num} **(1位 +{point[0] * mag[i]}点,  "
                                   f"2位 +{point[1] * mag[i]}点,  3位 +{point[2] * mag[i]}点)** (制限時間1分)")
            await asyncio.sleep(3)
            await ctx.channel.send(f"{constant.Question[f'Q{i + 1}']}")
            j, flag, winner, start = 1, False, [], datetime.now()
            while 0 <= j <= 3:
                reply = await client.wait_for('message')
                elap = (start - datetime.now()).seconds
                if reply.content == constant.Answer[f'A{i + 1}'] and reply.channel.id == constant.Quiz_room:
                    if reply.author.id not in winner:
                        winner.append(reply.author.id)
                        j, flag = j + 1, True
                elif (reply.content.lower() == "skip" and role_check_admin(reply)) or elap > 60:
                    await ctx.channel.send(f"問題{i + 1}はスキップされました (正解 : {constant.Answer[f'A{i + 1}']})")
                    j, flag = -1, False
                elif reply.content.lower() == "cancel" and role_check_admin(reply):
                    await ctx.channel.send(f"クイズを中断しました")
                    return
            if flag:
                await ctx.channel.send(f"正解者が出揃ったので問題{i + 1}を終了します (正解 : {constant.Answer[f'A{i + 1}']})")
            if len(winner) != 0:
                stc = ""
                for k in range(len(winner)):
                    stc += f"{k + 1}位 : {client.get_user(winner[k]).display_name} (+{point[k] * mag[i]}点)\n"
                await ctx.channel.send(f"**```問題{i + 1} 結果\n{stc}```**")
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
                    name = client.get_user(all_user[j]).display_name
                    embed.add_field(name=f"{i + 1}位", value=f"{name} ({all_result[i]}pts)")
                    ranker.append(all_user[j])
                    k += 1
            i += k
        await ctx.channel.send(embed=embed)
        await guild.get_member(ranker[0]).add_roles(role_W)
        await ctx.channel.send(f"クイズを終了しました\n{role_W.mention} → {guild.get_member(ranker[0]).mention}")
        await ctx.channel.send(f"{role_A.mention} `!out`で結果を {client.get_channel(constant.Result).mention} に出力")
        while True:
            reply = await client.wait_for('message', check=role_check_mode)
            if reply.content == "!out":
                await client.get_channel(constant.Result).send(embed=embed)
                break


load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
client.run(os.environ.get('TOKEN'))
