import discord
from discord.ext import tasks
from datetime import datetime
from pytz import timezone
import asyncio
import asyncio.exceptions
import random
import re
import os
import shutil
import copy
from dotenv import load_dotenv
import json
import sys
import jaconv
import constant
from zyanken import zyanken
from uno import uno_func
from uno import make_image
from uno import uno_record

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


# データを削除
async def delete_data(member):
    if member.guild.get_role(constant.Visitor) is not None:
        await client.get_user(member.id).ban(delete_message_days=0)
        await client.get_channel(constant.Test_room).send(f"{client.get_user(member.id).name}を削除しました")
    if str(member.id) in zyanken.Zyanken_data:
        zyanken.Zyanken_data.pop(str(member.id))
        with open('zyanken/zyanken_record.json', 'w') as f:
            json.dump(zyanken.Zyanken_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
    uno_record.data_delete(str(member.id))


@tasks.loop(minutes=1)
async def data_auto_save():
    with open('zyanken/zyanken_record.json', 'r') as f:
        before_zyanken_data = json.load(f)
    if zyanken.Zyanken_data != before_zyanken_data:
        if zyanken.File_backup is not None:
            await zyanken.File_backup.delete()
        with open('zyanken/zyanken_record.json', 'w') as f:
            json.dump(zyanken.Zyanken_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
        zyanken.File_backup = await client.get_channel(constant.Test_room).send(
            f"{time}\nData Auto Saved", file=discord.File('zyanken/zyanken_record.json'))
    data = "\n".join(zyanken.No_reply)
    with open('zyanken/no_reply_user.txt', 'w') as f:
        f.write(data)


@client.event
async def on_ready():
    data_auto_save.start()
    for type in ["point", "pointall"]:
        _, _, _, worst = zyanken.ranking_output(type, client.get_guild(constant.Server))
        if type == "point":
            zyanken.Former_loser_point = worst
        else:  # type == "pointall"
            zyanken.Former_loser_pointall = worst


@client.event
async def on_member_join(member):
    time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M')
    await client.get_channel(constant.Gate).send(f"{member.mention} が入室しました ({time})")


@client.event
async def on_member_remove(member):
    await delete_data(member)


@client.event
async def on_member_ban(_, member):
    await delete_data(member)


@client.event
async def on_message(ctx):
    guild = client.get_guild(constant.Server)

    def get_role(role_id):
        return discord.utils.get(guild.roles, id=role_id)

    def ng_check(ctx_wait):
        return all([ctx.channel.id == ctx_wait.channel.id, not ctx_wait.author.bot, ctx_wait.content != ""])

    def role_check_admin(ctx_role):
        return constant.Administrator in [roles.id for roles in ctx_role.author.roles]

    def role_check_mode(ctx_role):
        roles = [roles.id for roles in ctx_role.author.roles]
        return any([constant.Administrator in roles, constant.Moderator in roles])

    def role_check_visit(ctx_role):
        roles = [roles.id for roles in ctx_role.author.roles]
        return any([constant.Administrator in roles, constant.Moderator in roles, constant.Visitor in roles])

    if ctx.author.bot or ctx.content == "" or ctx.guild is None:  # BotのメッセージやDM、無入力(画像のみ)には反応させない
        return

    if ctx.content.lower() in ["_sd", "_shutdown"] and role_check_admin(ctx):
        with open('zyanken/zyanken_record.json', 'w') as f:
            json.dump(zyanken.Zyanken_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        await ctx.channel.send(file=discord.File('zyanken/zyanken_record.json'))
        await ctx.channel.send("Botをシャットダウンします")
        await client.logout()
        await sys.exit()

    if ctx.channel.id == constant.Gate:  # Gateでの入力チェック
        time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo'))
        password = f"_join {time.strftime('%Y/%m/%d')}"
        if ctx.content == password:
            await ctx.delete()
            await ctx.author.add_roles(get_role(constant.Visitor))
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
                if str(ctx.author.id) not in zyanken.No_reply:
                    await ctx.add_reaction(emoji1)
                    await ctx.add_reaction(emoji2)
                    await ctx.channel.send(f"{ctx.author.mention} {hand}\n**{msg}**",
                                           file=discord.File(img), delete_after=5.0)
                if constant.Challenger not in [roles.id for roles in ctx.author.roles]:
                    await guild.get_member(ctx.author.id).add_roles(get_role(constant.Challenger))
                break

    if ctx.content.split()[0].lower() in ["_nr", "_noreply"] and ctx.channel.id == constant.Zyanken_room:
        name = ctx.content[ctx.content.find(" ") + 1:].strip()
        if " " not in ctx.content.strip():
            name = guild.get_member(ctx.author.id).display_name
        for member in get_role(constant.Visitor).members:
            if name.lower() == member.display_name.lower():
                if str(member.id) not in zyanken.No_reply:
                    zyanken.No_reply.append(str(member.id))
                    await ctx.channel.send(f"{guild.get_member(member.id).mention} 返信を無効にしました")
                else:
                    await ctx.channel.send(f"{ctx.author.mention} 既に返信が無効になっています")
                return
        await ctx.channel.send(f"{ctx.author.mention} ユーザーが見つかりませんでした")

    if ctx.content.split()[0].lower() in ["_nrc", "_noreplycancel"] and ctx.channel.id == constant.Zyanken_room:
        name = ctx.content[ctx.content.find(" ") + 1:].strip()
        if " " not in ctx.content.strip():
            name = guild.get_member(ctx.author.id).display_name
        for member in get_role(constant.Visitor).members:
            if name.lower() == member.display_name.lower():
                if str(member.id) in zyanken.No_reply:
                    zyanken.No_reply.remove(str(member.id))
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
        for member in get_role(constant.Visitor).members:
            if name.lower() == member.display_name.lower():
                if str(member.id) in zyanken.Zyanken_data:
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
        input = ctx.content[ctx.content.find(" ") + 1:].strip()
        if input.split()[0].lower() in ["p", "point", "pa", "pointall"]:
            type = "point" if input.split()[0].lower() in ["p", "point"] else "pointall"
            try:
                num = int(re.sub(r'[^0-9]', "", input))
                if type == "point" and num >= 6:
                    num += 1
            except ValueError:
                num = 999
        else:
            await ctx.channel.send(f"{ctx.author.mention} 入力形式が間違っています\n"
                                   ">>> **_RanKing Type N**\nType = Point / PointAll\n"
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

        role_W, role_L = get_role(constant.Winner), get_role(constant.Loser)
        if type == "point":
            for member in role_W.members:
                await member.remove_roles(role_W)
            for user in best:
                await guild.get_member(user).add_roles(role_W)
            if zyanken.Former_loser_point != worst:
                if worst is not None:
                    await guild.get_member(worst).add_roles(role_L)
                if zyanken.Former_loser_point is not None:
                    await guild.get_member(zyanken.Former_loser_point).remove_roles(role_L)
            zyanken.Former_loser_point = worst
        else:  # type == "pointall"
            if zyanken.Former_loser_pointall != worst:
                await guild.get_member(worst).add_roles(role_L)
                await guild.get_member(zyanken.Former_loser_pointall).remove_roles(role_L)
            zyanken.Former_loser_pointall = worst

    if ctx.content in ["_rms", "_resetmystats"] and ctx.channel.id == constant.Zyanken_room:
        if str(ctx.author.id) in zyanken.Reset_user:
            return
        await ctx.channel.send(f"{ctx.author.mention} 戦績をリセットします.", delete_after=10.0)
        cnt = 0
        confirm = "本当に"
        msg = await ctx.channel.send(f"{ctx.author.mention} {confirm * cnt}よろしいですか？(Yes or No)")
        while True:
            reply = await client.wait_for('message', check=ng_check)
            if reply.content.lower() == "yes" and ctx.author.id == reply.author.id:
                cnt += 1
                await msg.delete()
                msg = await ctx.channel.send(f"{ctx.author.mention} {confirm * cnt}よろしいですか？(Yes or No)")
            elif reply.content.lower() == "no" and ctx.author.id == reply.author.id:
                await ctx.channel.send(f"{ctx.author.mention} キャンセルしました")
                return
            if cnt >= 10:
                if str(ctx.author.id) in zyanken.Zyanken_data:
                    zyanken.Zyanken_data.pop(str(ctx.author.id))
                zyanken.Reset_user.append(str(ctx.author.id))
                await ctx.channel.send(f"{ctx.author.mention} リセット完了しました")
                break

    if ctx.content in ["_ss", "_statssave"] and role_check_mode(ctx):
        with open('zyanken/zyanken_record.json', 'w') as f:
            json.dump(zyanken.Zyanken_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        data = "\n".join(zyanken.No_reply)
        with open('zyanken/no_reply_user.txt', 'w') as f:
            f.write(data)
        data = "\n".join(zyanken.Reset_user)
        with open('zyanken/reset_user.txt', 'w') as f:
            f.write(data)
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

    if ctx.content.split()[0].lower() in ["_rm", "_remove"] and role_check_admin(ctx):  # 参加者を削除する
        name = ctx.content[ctx.content.find(" ") + 1:].strip()
        for member in get_role(constant.Visitor).members:
            if name.lower() == member.display_name.lower():
                if str(member.id) in constant.Joiner:
                    constant.Joiner.remove(member.id)
                    await ctx.channel.send(f"{member.display_name}を削除しました")
                else:
                    await ctx.channel.send(f"{member.display_name}は参加していません")
                return
        await ctx.channel.send("ユーザーが見つかりませんでした")

    if ctx.channel.id == constant.Recruit and ctx.content.lower() in ["_l", "_list"]:  # 参加希望者を表示する
        if len(constant.Joiner) >= 1:
            stc = [f"{i + 1}. {client.get_user(constant.Joiner[i]).display_name}\n"
                   for i in range(len(constant.Joiner))]
            await ctx.channel.send(f"参加希望者リスト\n```{''.join(stc)}```", delete_after=20.0)
        else:
            await ctx.channel.send("参加希望者はいません", delete_after=20.0)

    if ctx.content.split()[0].lower() in ["_pu", "_pickup"] and role_check_mode(ctx):  # 参加希望者の抽選を行う
        try:
            role_P = get_role(constant.Participant)
            num = int(re.sub(r'[^0-9]', "", ctx.content))
            pick_num = sorted(random.sample(list(range(len(constant.Joiner))), num))  # 抽選を行う
            stc = [f"{i + 1}. {guild.get_member(constant.Joiner[pick_num[i]]).display_name}\n"
                   for i in range(len(pick_num))]
            for i in pick_num:
                await guild.get_member(constant.Joiner[i]).add_roles(role_P)
            await ctx.channel.send(f"参加者リスト 抽選結果\n```{''.join(stc)}```"
                                   f"リストのユーザーにロール {role_P.mention} を付与しました\n"
                                   f"配信用ボイスチャンネルに接続出来るようになります")
            constant.Joiner = []
        except ValueError:
            await ctx.channel.send("入力エラー")

    if ctx.content.split()[0].lower() in ["_rs", "_reset"] and role_check_mode(ctx):  # ロールをリセットする
        role_name = ctx.content[ctx.content.find(" ") + 1:].strip().lower()
        if role_name in ["participant", "p"]:
            rm_role = get_role(constant.Participant)
            constant.Joiner = []
        elif role_name in ["winner", "w"]:
            rm_role = get_role(constant.Winner)
        elif role_name in ["loser", "l"]:
            rm_role = get_role(constant.Loser)
        elif role_name in ["challenger", "c"]:
            rm_role = get_role(constant.Challenger)
        else:
            await ctx.channel.send(f"{ctx.author.mention} RoleNameを入力してください\n"
                                   ">>> **_ReSet RoleName**\nRoleName = Participant / Winner / Loser / Challenger")
            return
        for member in rm_role.members:
            await member.remove_roles(rm_role)
        await ctx.channel.send(f"ロール {rm_role.mention} をリセットしました")

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
                reply = await client.wait_for('message', check=ng_check)
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
                    reply = await client.wait_for('message', check=ng_check)
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
                stc = [f"[Q{i + 1}] {constant.Question[f'Q{i + 1}']}\n→ {constant.Answer[f'A{i + 1}']}\n"
                       for i in range(len(constant.Question))]
                await ctx.channel.send(f"```{''.join(stc)}```")
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
                elif (reply.content.lower() == "!skip" and role_check_admin(reply)) or elap > 60:
                    await ctx.channel.send(f"問題{i + 1}はスキップされました (正解 : {constant.Answer[f'A{i + 1}']})")
                    j, flag = -1, False
                elif reply.content.lower() == "!cancel" and role_check_admin(reply):
                    await ctx.channel.send(f"クイズを中断しました")
                    return
            if flag:
                await ctx.channel.send(f"正解者が出揃ったので問題{i + 1}を終了します (正解 : {constant.Answer[f'A{i + 1}']})")
            if len(winner) != 0:
                stc = [f"{k + 1}位 : {client.get_user(winner[k]).display_name} (+{point[k] * mag[i]}点)\n"
                       for k in range(len(winner))]
                await ctx.channel.send(f"**```問題{i + 1} 結果\n{''.join(stc)}```**")
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
        role_A, role_W = get_role(constant.Administrator), get_role(constant.Winner)
        await ctx.channel.send(embed=embed)
        await guild.get_member(ranker[0]).add_roles(role_W)
        await ctx.channel.send(f"クイズを終了しました\n{role_W.mention} → {guild.get_member(ranker[0]).mention}")
        await ctx.channel.send(f"{role_A.mention} `!out`で結果を {client.get_channel(constant.Result).mention} に出力")
        while True:
            reply = await client.wait_for('message', check=role_check_mode)
            if reply.content == "!out":
                await client.get_channel(constant.Result).send(embed=embed)
                break

    async def send_card(n, times, send_flag):
        # 前に送ったDMがあるなら削除
        if all_data[n][2] is not None:
            await all_data[n][2].delete()
        add_card = uno_func.deal_card(times)
        all_data[n][1] = uno_func.sort_card(all_data[n][1] + add_card)
        # 手札が1枚以上なら画像を作成/送信
        if all_data[n][1]:
            make_image.make_hand(all_data[n][1])
            if uno_func.card_to_string(add_card) == "なし" or not send_flag:
                card_msg = ""
            else:
                card_msg = f"追加カード↓```{uno_func.card_to_string(uno_func.sort_card(add_card))}```"
            card_msg += f"現在の手札↓```{uno_func.card_to_string(all_data[n][1])}```"
            all_data[n][2] = await client.get_user(all_data[n][0]).send(card_msg, file=discord.File('uno/hand.png'))
            os.remove('uno/hand.png')
        else:
            card_msg = "手札が全て無くなりました"
            all_data[n][2] = await client.get_user(all_data[n][0]).send(card_msg,
                                                                        file=discord.File('uno/Background.png'))

    if ctx.content.lower() in ["_us", "_unostart"] and ctx.channel.id == constant.UNO_room and not uno_func.UNO_start:
        uno_func.UNO_start = True
        role_U = get_role(constant.UNO_Player)
        await ctx.channel.send("UNOを開始します\n※必ずダイレクトメッセージの送信を許可にしてください\n"
                               "参加する方は `!Join` と入力してください ( `!End` で締め切り, `!Cancel` で中止)")
        player = []
        while True:
            reply = await client.wait_for('message', check=ng_check)
            input = jaconv.z2h(reply.content, ascii=True).lower()
            if input in ["!j", "!join"] and reply.author.id not in player:
                player.append(reply.author.id)
                await guild.get_member(reply.author.id).add_roles(role_U)
                await ctx.channel.send(f"{reply.author.mention} 参加しました", delete_after=5.0)
            elif input in ["!e", "!end"] and player:
                break
            elif reply.content == "!cancel":
                await ctx.channel.send("中止しました")
                uno_func.UNO_start = False
                return
        stc = [f"{i + 1}. {guild.get_member(player[i]).display_name}\n" for i in range(len(player))]
        await ctx.channel.send(f"```プレイヤーリスト\n\n{''.join(stc)}```締め切りました\t次に初期手札の枚数を入力してください")
        while True:
            reply = await client.wait_for('message', check=ng_check)
            input = jaconv.z2h(reply.content, ascii=True, digit=True).lower()
            if input == "!cancel":
                await ctx.channel.send("中止しました")
                uno_func.UNO_start = False
                return
            try:
                num = int(re.sub(r'[^0-9]', "", input))
                if 2 <= num <= 100:
                    await ctx.channel.send(f"初期手札を{num}枚で設定しました")
                    break
                else:
                    await ctx.channel.send(f"2～100枚以内で指定してください", delete_after=5.0)
            except ValueError:
                await ctx.channel.send(f"{reply.author.mention} 入力が正しくありません", delete_after=3.0)

        random.shuffle(player)
        # all_data == [id, 手札リスト, DM変数, [UNOフラグ, フラグが立った時間]] × 人数分
        all_data = [[id, [], None, [False, None]] for id in player]
        for i in range(len(player)):
            try:
                await send_card(i, num, False)
            except:
                await ctx.channel.send(f"{client.get_user(player[i]).mention} DMを許可していないのでエラーが発生しました\n"
                                       f"最初からやり直してください")
                return
        await ctx.channel.send(f"カードを配りました\nBotからのDMを確認してください")
        await ctx.channel.send(f"ルール設定や手札の出し方など↓```{uno_func.Rule}```")
        stc = [f"{i + 1}. {guild.get_member(player[i]).display_name}\n" for i in range(len(player))]
        await ctx.channel.send(f"ゲームの進行順は以下のようになります```{''.join(stc)}```")
        cnt, card, flag, penalty, winner, msg1, msg2 = 0, uno_func.first_card(), False, 0, None, None, None
        shutil.copy('uno/Area.png', 'uno/Area_tmp.png')
        make_image.make_area(card[-1])
        await ctx.channel.send(f"{role_U.mention} ゲームを始めてもよろしいですか？(1分以上経過 or 全員が `!OK` で開始)")
        cnt_ok, ok_player, ok_start = 0, [], datetime.now()
        while True:
            try:
                reply = await client.wait_for('message',
                                              check=ng_check, timeout=60.0 - (datetime.now() - ok_start).seconds)
            except asyncio.exceptions.TimeoutError:
                break
            if reply.author.id in player and reply.author.id not in ok_player:
                if jaconv.z2h(reply.content, ascii=True).lower() == "!ok":
                    cnt_ok += 1
                    ok_player.append(reply.author.id)
            if cnt_ok == len(player):
                break

        while True:
            i, flag, get_flag, drop_flag = cnt % len(all_data), False, True, False
            all_player = [all_data[j][0] for j in range(len(all_data))]
            time = len(all_data[i][1]) * 5 + 5
            time = 30 if time < 30 else 60 if time > 60 else time
            if msg1 is not None:
                await msg1.delete()
                await msg2.delete()
            stc = [f"{j + 1}. {guild.get_member(all_data[j][0]).display_name} : {len(all_data[j][1])}枚\n"
                   for j in range(len(all_data))]
            msg1 = await ctx.channel.send(f"```\n各プレイヤーの現在の手札枚数\n\n{''.join(stc)}```"
                                          f"__現在の場札のカード : {card[-1]}__", file=discord.File('uno/Area_tmp.png'))
            msg2 = await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} の番です (制限時間{time}秒)")
            # 記号しか無いかチェック
            while True:
                if all([uno_func.card_to_id(j) % 100 > 9 for j in all_data[i][1]]):
                    await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} 記号残りなので2枚追加されます",
                                           delete_after=10.0)
                    await send_card(i, 2, True)
                else:
                    break
            # カード入力処理
            start = datetime.now()
            while True:
                try:
                    reply = await client.wait_for('message', check=ng_check,
                                                  timeout=float(time) - (datetime.now() - start).seconds)
                    input = jaconv.z2h(jaconv.h2z(reply.content), kana=False, ascii=True, digit=True).lower()
                except asyncio.exceptions.TimeoutError:
                    await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} 時間切れとなったので強制スキップします",
                                           delete_after=10.0)
                    break
                # UNOの指摘/宣言
                if "!uno" in input:
                    if len(reply.raw_mentions) == 1:
                        j = uno_func.search_player(reply.raw_mentions[0], all_data)
                        if j is not None:
                            # UNOフラグが立ってから10秒以上経過
                            if all_data[j][3][0] and (datetime.now() - all_data[j][3][1]).seconds >= 10:
                                all_data[j][3] = [False, None]
                                await ctx.channel.send(f"{client.get_user(all_data[j][0]).mention} "
                                                       f"UNOと言っていないのでペナルティーで2枚追加されます", delete_after=10.0)
                                await send_card(j, 2, True)
                            else:
                                await ctx.channel.send(f"{reply.author.mention} "
                                                       f"今はそのユーザーへのUNOの指摘は無効となっています", delete_after=10.0)
                        else:
                            await ctx.channel.send(f"{reply.author.mention} そのユーザーはゲームに参加していません",
                                                   delete_after=5.0)
                    else:
                        j = uno_func.search_player(reply.author.id, all_data)
                        if j is not None:
                            # 自分のUNOフラグが立っている場合
                            if all_data[j][3][0]:
                                all_data[j][3] = [False, None]
                                await ctx.channel.send(f"{role_U.mention}  {reply.author.mention}がUNOを宣言しました")
                            elif len(all_data[j][1]) >= 2:
                                await ctx.channel.send(f"{reply.author.mention} 今はUNOを宣言しても意味がありません")
                            else:
                                await ctx.channel.send(f"{reply.author.mention} 既にUNOと宣言済みです")
                # 途中参加
                elif input in ["!j", "!join"] and reply.author.id not in all_player:
                    all_player.append(reply.author.id)
                    all_data.append([reply.author.id, [], None, [False, None]])
                    await send_card(-1, num, False)
                    await guild.get_member(reply.author.id).add_roles(role_U)
                    await ctx.channel.send(f"{role_U.mention}  {reply.author.mention}が途中参加しました")
                # ゲームから棄権する
                elif "!drop" in input and reply.author.id in all_player:
                    # 棄権者を指定
                    if len(all_data) > 2 and len(reply.raw_mentions) == 1 and role_check_mode(reply):
                        j = uno_func.search_player(reply.raw_mentions[0], all_data)
                        if j is not None:
                            await guild.get_member(all_data[j][0]).remove_roles(role_U)
                            await ctx.channel.send(f"{role_U.mention}  "
                                                   f"{client.get_user(all_data[j][0]).mention}を棄権させました")
                            if j <= i:
                                cnt -= 1
                            uno_record.add_penalty(all_data[j][0], all_data[j][1])
                            all_data.pop(j)
                            drop_flag = True
                            break
                        else:
                            await ctx.channel.send(f"{reply.author.mention} そのユーザーはゲームに参加していません",
                                                   delete_after=5.0)
                    # 自分が棄権する
                    elif len(all_data) > 2 and len(reply.raw_mentions) == 0:
                        await guild.get_member(reply.author.id).remove_roles(role_U)
                        j = uno_func.search_player(reply.author.id, all_data)
                        if j <= i:
                            cnt -= 1
                        uno_record.add_penalty(all_data[j][0], all_data[j][1])
                        all_data.pop(j)
                        await ctx.channel.send(f"{role_U.mention}  {reply.author.mention}が棄権しました")
                        drop_flag = True
                        break
                    else:
                        await ctx.channel.send(f"{reply.author.mention} "
                                               f"2人以下の状態では棄権出来ません(`!Cancel` で中止)", delete_after=5.0)
                # ゲームを強制中止する
                elif input == "!cancel" and reply.author.id in all_player:
                    await ctx.channel.send(f"{role_U.mention} ゲームを中止しますか？(全員が `!OK` で中止、`!NG` でキャンセル)")
                    cnt_cancel, cancel_player, cancel_start = 0, [], datetime.now()
                    while True:
                        try:
                            confirm = await client.wait_for('message', check=ng_check,
                                                            timeout=30.0 - (datetime.now() - cancel_start).seconds)
                            input = jaconv.z2h(confirm.content, ascii=True).lower()
                        except asyncio.exceptions.TimeoutError:
                            await ctx.channel.send(f"{role_U.mention} 時間切れでキャンセルしました")
                            break
                        if confirm.author.id in all_player and confirm.author.id not in cancel_player:
                            if input == "!ok":
                                cnt_cancel += 1
                                cancel_player.append(confirm.author.id)
                            elif input == "!ng":
                                await ctx.channel.send(f"{role_U.mention} キャンセルしました")
                                break
                        if cnt_cancel == len(all_player):
                            os.remove('uno/Area_tmp.png')
                            for member in role_U.members:
                                await member.remove_roles(role_U)
                            uno_func.UNO_start = False
                            await ctx.channel.send(f"{role_U.mention} ゲームを中止しました")
                            return
                # 自分のターンでの行動
                elif reply.author.id == all_data[i][0]:
                    # 山札から1枚引く
                    if input in ["!g", "!get"]:
                        if get_flag:
                            await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} "
                                                   f"山札から1枚引きます", delete_after=5.0)
                            await send_card(i, 1, True)
                            get_flag = False
                        else:
                            await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} "
                                                   f"山札から引けるのは1度のみです", delete_after=5.0)
                    # カードを出さない
                    elif input in ["!p", "!pass"]:
                        if penalty > 0 or not get_flag:
                            await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} "
                                                   f"パスしました", delete_after=5.0)
                        else:
                            await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} "
                                                   f"山札から1枚引いてパスしました", delete_after=5.0)
                            await send_card(i, 1, True)
                        break
                    else:
                        # 出せるカードかチェック
                        check, error = uno_func.check_card(
                            card[-1], uno_func.string_to_card(input), all_data[i][1], penalty)
                        if check:
                            # 出したカードを山場に追加
                            bet_card = uno_func.string_to_card(input)
                            card += bet_card
                            # 出したカードを手札から削除して送信 & 場札更新
                            for j in bet_card:
                                all_data[i][1].remove(j)
                                make_image.make_area(j)
                            await send_card(i, 0, True)
                            flag = True
                            break
                        else:
                            await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} {error}",
                                                   delete_after=5.0)
            # 棄権時は以下の処理を飛ばす
            if drop_flag:
                continue
            # ドロー2/4のペナルティー枚数計算
            if flag:
                penalty += uno_func.calculate_penalty(uno_func.string_to_card(input))
            # ワイルドカードを出した後の色指定
            if card[-1] in ["ワイルド", "ドロー4"] and flag:
                msg = await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} カラーを指定してください (制限時間20秒)")
                start = datetime.now()
                while True:
                    try:
                        color = await client.wait_for('message', check=ng_check,
                                                      timeout=20.0 - (datetime.now() - start).seconds)
                        input = jaconv.z2h(color.content, ascii=True).lower()
                    except asyncio.exceptions.TimeoutError:
                        await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} 時間切れなのでランダムで決めます",
                                               delete_after=10.0)
                        card[-1] = f"{uno_func.Color[random.randint(0, 3)]}{card[-1]}"
                        break
                    if color.author.id == all_data[i][0] and uno_func.translate_input(input) in uno_func.Color:
                        card[-1] = f"{uno_func.translate_input(input)}{card[-1]}"
                        break
                await msg.delete()
            # ドロー2/4のペナルティーを受ける
            elif penalty > 0 and not flag:
                await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} ペナルティーで{penalty}枚追加されました",
                                       delete_after=10.0)
                await send_card(i, penalty, True)
                penalty, cnt, = 0, cnt - 1
            # スキップ処理
            elif card[-1][1:] == "スキップ" and flag:
                skip_n = len(uno_func.string_to_card(input))
                await ctx.channel.send(f"{2 * skip_n - 1}人スキップします", delete_after=10.0)
                cnt += 2 * skip_n - 1
            # リバース処理
            elif card[-1][1:] == "リバース" and flag:
                reverse_n = len(uno_func.string_to_card(input))
                await ctx.channel.send(f"{reverse_n}回リバースします", delete_after=10.0)
                if reverse_n % 2 == 1:
                    # リバースを出した人のリバースされた配列中の位置を代入
                    tmp = copy.copy(all_data[i][0])
                    all_data.reverse()
                    cnt = uno_func.search_player(tmp, all_data)
            # 上がり
            if not all_data[i][1] and not all_data[i][3][0]:
                await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} YOU WIN!")
                await guild.get_member(all_data[i][0]).add_roles(get_role(constant.Winner))
                winner = i
                break
            # 手札は0枚になったがUNO宣言忘れ
            elif not all_data[i][1] and all_data[i][3][0]:
                await ctx.channel.send(f"{client.get_user(all_data[i][0]).mention} UNO宣言忘れのペナルティーで2枚追加します",
                                       delete_after=10.0)
                await send_card(i, 2, True)
                all_data[i][3] = [False, None]
            # 残り1枚になったらUNOフラグを立てる
            elif len(all_data[i][1]) == 1 and not all_data[i][3][0]:
                all_data[i][3] = [True, datetime.now()]
            cnt += 1

        # 点数計算
        all_pts, stc = [], ""
        for i in range(len(all_data)):
            pts = uno_record.calculate_point(all_data[i][1])
            all_data[i].append(pts)
            all_pts.append(pts)
        # 1位には他ユーザーの合計得点をプラス
        all_data[winner][4] = sum(all_pts) * -1
        sort_data = sorted(all_data, key=lambda x: x[4], reverse=True)
        for i in range(len(sort_data)):
            stc += f"{i + 1}位 : {guild.get_member(sort_data[i][0]).display_name} ({sort_data[i][4]}pts)\n"
            stc += f"残り手札【{uno_func.card_to_string(sort_data[i][1])}】\n\n"
        await ctx.channel.send(f"```\n★ゲーム結果\n\n{stc}```{role_U.mention} 結果を記録してゲームを終了しました")
        uno_record.data_save(all_data)
        os.remove('uno/Area_tmp.png')
        for member in role_U.members:
            await member.remove_roles(role_U)
        uno_func.UNO_start = False

    if ctx.content.split()[0].lower() in ["_rc", "_record"]:  # プレイヤーのUNO戦績を表示
        if ctx.channel.id != constant.UNO_room and not role_check_mode(ctx):  # UNO会場のみ反応(モデレーター以外)
            return
        name = ctx.content[ctx.content.find(" ") + 1:].strip()
        if " " not in ctx.content.strip():
            name = guild.get_member(ctx.author.id).display_name
        data, url, user, id = [], None, None, None
        for member in get_role(constant.Visitor).members:
            if name.lower() == member.display_name.lower():
                data, url = uno_record.record_output(member.id)
                user, id = member.display_name, member.id
        if data is None:
            await ctx.channel.send(f"{ctx.author.mention} データが記録されていません")
            return
        embed = discord.Embed(title=user, color=0xFF3333)
        embed.set_author(name='UNO Records', icon_url=client.get_user(id).avatar_url)
        embed.set_thumbnail(url=url)
        embed.add_field(name="総得点", value=f"{data[2]}点")
        embed.add_field(name="勝率", value=f"{data[3]:.01f}% ({data[4] + data[5]}戦 {data[4]}勝{data[5]}敗)")
        embed.add_field(name="直近5戦", value=f"{data[9]}点")
        embed.add_field(name="最高獲得点", value=f"{data[6]}点")
        embed.add_field(name="最低獲得点", value=f"{data[7]}点")
        embed.add_field(name="ペナルティー", value=f"{data[8]}点")
        await ctx.channel.send(embed=embed)

    if ctx.content.split()[0].lower() in ["_cdm", "_cleardm"] and ctx.channel.id == constant.UNO_room:  # BotとのDMを全削除
        try:
            msg = await ctx.channel.send(f"{ctx.author.mention} BotとのDMを削除中...")
            messages = await client.get_user(ctx.author.id).history(limit=None).flatten()
            for message in messages:
                if message.author.id != ctx.author.id:
                    await message.delete()
            await msg.delete()
            await ctx.channel.send(f"{ctx.author.mention} 削除が完了しました")
        except:
            await ctx.channel.send(f"{ctx.author.mention} DMが開放されていないので削除できません")


load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
client.run(os.environ.get('TOKEN'))
