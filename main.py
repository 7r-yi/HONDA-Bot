import discord
from datetime import datetime
import asyncio
import json
import random
import os
from os.path import join, dirname
from dotenv import load_dotenv
import constant

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
TOKEN = os.environ.get('TOKEN')
client = discord.Client()


@client.event
async def on_message(ctx):
    def bot_check(ctx_wait):
        return not ctx_wait.author.bot

    if ctx.channel.id == constant.Gate and ctx.author.id != constant.System and not ctx.author.bot:  # Gateでの入力チェック
        password = f"_join {datetime.now().strftime('%Y/%m/%d')}"
        await ctx.delete()
        if ctx.content == password:
            role = discord.utils.get(ctx.guild.roles, id=constant.Visitor)
            await ctx.author.add_roles(role)
            await ctx.channel.send(f'{ctx.author.mention} 入室しました')
        else:
            msg = await ctx.channel.send(f'{ctx.author.mention} 入室コマンドが違います')
            await asyncio.sleep(5)
            await msg.delete()

    if ctx.channel.id == constant.Recruit and ctx.content.lower() in ["_c", "_can"]:  # 参加希望を出す
        if ctx.author.id not in constant.joiner:
            constant.joiner.append(ctx.author.id)
            msg = await ctx.channel.send(f'{ctx.author.mention} 参加希望者リストに追加しました')
        else:
            msg = await ctx.channel.send(f'{ctx.author.mention} すでに参加希望が出されています')
        await asyncio.sleep(5)
        await msg.delete()

    if ctx.channel.id == constant.Recruit and ctx.content.lower() in ["_d", "_drop"]:  # 参加希望を取り消す
        if ctx.author.id in constant.joiner:
            constant.joiner.remove(ctx.author.id)
            msg = await ctx.channel.send(f'{ctx.author.mention} 参加希望を取り消しました')
        else:
            msg = await ctx.channel.send(f'{ctx.author.mention} 参加希望が出されていません')
        await asyncio.sleep(5)
        await msg.delete()

    if ctx.channel.id == constant.Recruit and ctx.content.lower() in ["_l", "_list"]:  # 参加希望者を表示する
        if len(constant.joiner) >= 1:
            str = "参加希望者リスト\n```"
            for i in range(len(constant.joiner)):
                str += f"{i + 1}. {client.get_user(constant.joiner[i]).display_name}\n"
            str += "```"
        else:
            str = "参加希望者はいません"
        msg = await ctx.channel.send(str)
        await asyncio.sleep(20)
        await msg.delete()

    if ctx.content.split(" ")[0].lower() in ["_pu", "_pickup"]:  # 参加希望者の抽選を行う
        if 'Administrator' not in [i.name for i in ctx.author.roles]:
            return

        try:
            num = int(ctx.content[ctx.content.find(" ") + 1:])
            num_list = list(range(len(constant.joiner)))
            pick_num = sorted(random.sample(num_list, num))
            str = "参加者リスト 抽選結果\n```"
            for i in pick_num:
                str += f"{i + 1}. {client.get_user(constant.joiner[i]).display_name}\n"
            str += "```"
            guild = client.get_guild(constant.Server)
            role = discord.utils.get(ctx.guild.roles, id=constant.Participant)
            for i in pick_num:
                await guild.get_member(constant.joiner[i]).add_roles(role)
            await ctx.channel.send(f"{str}リストのユーザーにロール {role.mention} を付与しました\n"
                                   f"配信用ボイスチャンネルに接続出来るようになります")
            constant.joiner = []
        except ValueError:
            await ctx.channel.send("入力エラー")

    if ctx.content.lower() in ["_r", "_reset"]:  # ロールParticipantをリセットする
        if 'Administrator' not in [i.name for i in ctx.author.roles]:
            return

        role = discord.utils.get(ctx.guild.roles, id=constant.Participant)
        for member in role.members:
            if member.id != constant.Shichi:
                await member.remove_roles(role)
        constant.joiner = []
        await ctx.channel.send(f"ロール {role.mention} をリセットしました")

    if ctx.content.lower() in ["_qs", "_quizstart"]:
        if 'Administrator' not in [i.name for i in ctx.author.roles]:
            return

        with open('quiz.json', encoding="utf-8") as file:
            quiz = json.load(file)
        await ctx.channel.send("クイズを開始します")

        for i in range(1, 11):
            await ctx.channel.send(f"Next →　問題{i}/10")
            j, winner = 1, []
            while j <= 3:
                reply = await client.wait_for('message', check=bot_check)
                if reply.content == quiz[f"Q{i}"] and reply.author.id not in winner:
                    winner.append(reply.author.id)
                    j += 1
            await ctx.channel.send(f"正解者が出揃ったので問題{i}を終了します\n(正解 : {quiz[f'Q{i}']})")
            for k in range(3):
                if winner[k] not in constant.result:
                    constant.result[winner[k]] = constant.point[k]
                else:
                    new_pts = constant.result[winner[k]] + constant.point[k]
                    constant.result[winner[k]] = new_pts
            await asyncio.sleep(3)

        all_user, all_result = list(constant.result.keys()), sorted(list(constant.result.values()), reverse=True)
        ranker = []
        str = "集計結果\n```"
        for i in range(5):
            for j in range(len(all_user)):
                if constant.result[all_user[j]] == all_result[i]:
                    str += f"{i + 1}位 : {client.get_user(all_user[j]).display_name} ({all_result[i]}pts)\n"
                    ranker.append(all_user[j])
        str += "```"
        guild = client.get_guild(constant.Server)
        role = discord.utils.get(ctx.guild.roles, id=constant.Winner)
        await guild.get_member(ranker[0]).add_roles(role)
        await ctx.channel.send(f"{str}クイズを終了しました\n"
                               f"{guild.get_member(ranker[0]).mention} にロール {role.mention} を付与しました\n"
                               f"{client.get_channel(constant.Winner_room).mention} にアクセス出来るようになります")
        constant.result = {}


client.run(TOKEN)
