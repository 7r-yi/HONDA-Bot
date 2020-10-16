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
        await ctx.delete()
        password = f"_join {datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d')}"
        if ctx.content == password:
            role = discord.utils.get(ctx.guild.roles, id=constant.Visitor)
            await ctx.author.add_roles(role)
            await ctx.channel.send(f'{ctx.author.mention} 参加しました')
        else:
            msg = await ctx.channel.send(f'{ctx.author.mention} コマンドが違います')
            await asyncio.sleep(5)
            await msg.delete()

    if not role_check_visit(ctx):  # 以下、@everyoneは実行不可
        return

    if ctx.content in ["グー", "チョキ", "パー"] and not ctx.author.bot:
        img, hand, msg, emoji1, emoji2 = zyanken.honda_to_zyanken(ctx.content)
        await ctx.add_reaction(emoji1)
        await ctx.add_reaction(emoji2)
        msg1 = await ctx.channel.send(f"{ctx.author.mention} {hand}", file=discord.File(img))
        msg2 = await ctx.channel.send(f"**{msg}**")
        await asyncio.sleep(10)
        await msg1.delete()
        await msg2.delete()

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
            str = "参加希望者リスト\n```"
            for i in range(len(constant.Joiner)):
                str += f"{i + 1}. {client.get_user(constant.Joiner[i]).display_name}\n"
            str += "```"
        else:
            str = "参加希望者はいません"
        msg = await ctx.channel.send(str)
        await asyncio.sleep(20)
        await msg.delete()

    if ctx.content.split(" ")[0].lower() in ["_pu", "_pickup"] and role_check_mode(ctx):  # 参加希望者の抽選を行う
        try:
            num = int(ctx.content[ctx.content.find(" ") + 1:])
            num_list = list(range(len(constant.Joiner)))
            pick_num = sorted(random.sample(num_list, num))
            str = "参加者リスト 抽選結果\n```"
            for i in pick_num:
                str += f"{i + 1}. {client.get_user(constant.Joiner[i]).display_name}\n"
            str += "```"
            guild = client.get_guild(constant.Server)
            role = discord.utils.get(ctx.guild.roles, id=constant.Participant)
            for i in pick_num:
                print(guild.get_member(constant.Joiner[i]))
                await guild.get_member(constant.Joiner[i]).add_roles(role)
            await ctx.channel.send(f"{str}リストのユーザーにロール {role.mention} を付与しました\n"
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

    if ctx.content.lower() in ["_qe", "_quizentry"] and role_check_admin(ctx):
        await ctx.channel.send("クイズの問題を登録します(Backで1問前に戻る、Skipで次の問題へ、Cancelで中断)")
        i = 0
        while i < 10:
            await ctx.channel.send(f"**{i + 1}**/10問目の解答を入力してください")
            reply = (await client.wait_for('message', check=bot_check)).content
            if reply.lower() == "back" and i >= 1:
                await ctx.channel.send(f"{i}問目の登録に戻ります")
                i -= 1
            elif reply.lower() == "skip":
                await ctx.channel.send(f"{i + 1}問目の登録をスキップします")
                i += 1
            elif reply.lower() == "cancel":
                await ctx.channel.send("問題の登録を中断しました")
                return
            else:
                constant.Question[f"Q{i + 1}"] = reply
                await ctx.channel.send(f"{i + 1}問目の問題文を登録しました\n解答を入力してください")
                reply = (await client.wait_for('message', check=bot_check)).content
                if reply.lower() == "back" and i >= 1:
                    await ctx.channel.send(f"{i}問目の登録に戻ります")
                    i -= 1
                elif reply.lower() == "cancel":
                    await ctx.channel.send("問題の登録を中断しました")
                    return
                else:
                    constant.Answer[f"A{i + 1}"] = reply
                    await ctx.channel.send(f"{i + 1}問目の解答を登録しました")
                    i += 1
        await ctx.channel.send(f"全ての問題の登録が完了しました")

    if ctx.content.lower() in ["_qr", "_quizreset"] and role_check_admin(ctx):
        await ctx.channel.send("クイズの問題を全消去します. よろしいですか？(Yes/No)")
        reply = (await client.wait_for('message', check=bot_check)).content
        if reply.lower() == "yes":
            constant.Question = {}
            constant.Answer = {}
            await ctx.channel.send("消去しました")
        else:
            await ctx.channel.send("キャンセルしました")
            return

    if ctx.content.lower() in ["_qs", "_quizstart"] and role_check_admin(ctx):
        result = {}
        point = [4, 2, 1]
        mag = [1, 1, 1, 1, 2, 1, 1, 1, 1, 3]
        await ctx.channel.send("クイズを開始します")

        for i in range(10):
            await ctx.channel.send(f"問題**{i + 1}**/10 **(1位 +{point[0] * mag[i]}点,  "
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
                for k in range(3):
                    if winner[k] not in result:
                        result[winner[k]] = point[k] * mag[i]
                    else:
                        new_pts = result[winner[k]] + point[k] * mag[i]
                        result[winner[k]] = new_pts
            await asyncio.sleep(5)

        all_user, all_result = list(result.keys()), sorted(list(result.values()), reverse=True)
        ranker = []
        str = "集計結果\n```"
        for i in range(5):
            for j in range(len(all_user)):
                if result[all_user[j]] == all_result[i]:
                    str += f"{i + 1}位 : {client.get_user(all_user[j]).display_name} ({all_result[i]}pts)\n"
                    ranker.append(all_user[j])
        str += "```"
        guild = client.get_guild(constant.Server)
        role = discord.utils.get(ctx.guild.roles, id=constant.Winner)
        await guild.get_member(ranker[0]).add_roles(role)
        await ctx.channel.send(f"{str}クイズを終了しました\n"
                               f"{guild.get_member(ranker[0]).mention} にロール {role.mention} を付与しました\n"
                               f"{client.get_channel(constant.Winner_room).mention} にアクセス出来るようになります")


keep_alive.keep_alive()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
client.run(os.environ.get('TOKEN'))
