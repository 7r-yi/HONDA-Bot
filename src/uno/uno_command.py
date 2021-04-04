import discord
from discord.ext import commands
from discord.errors import Forbidden, DiscordServerError, HTTPException
import aiohttp
import asyncio
import asyncio.exceptions
import os
import traceback
import shutil
import copy
import random
import collections
import jaconv
from datetime import datetime
from pytz import timezone
import re
import constant as cs
from multi_func import get_role, role_check_admin, role_check_mode
from . import uno_func as uf
from . import make_image as mi
from . import uno_record as ur

WATCH_FLAG = None
ALL_DATA, ALL_PLAYER, INITIAL_NUM, TURN, DECLARATION_WAIT, JOINING_WAIT = [], [], 7, 0, False, True


# ゲーム終了処理 (画像やロール削除)
async def uno_end(guild, image_flag=False, new_flag=False):
    global ALL_DATA, ALL_PLAYER, INITIAL_NUM, JOINING_WAIT
    if image_flag:
        os.remove(mi.AREA_COPY_PASS)
    # 新規プレイヤーにはUNOロール付与
    if new_flag:
        for player in ALL_PLAYER:
            if cs.UNO not in [roles.id for roles in guild.get_member(player).roles]:
                await guild.get_member(player).add_roles(get_role(guild, cs.UNO))
    uf.UNO_start = False
    ALL_DATA, ALL_PLAYER, INITIAL_NUM, JOINING_WAIT = [], [], 7, True


# ゲーム開始処理
async def run_uno_config(bot, ctx, type):
    try:
        await run_uno(bot, ctx, type)
    except DiscordServerError or HTTPException or aiohttp.ClientOSError:
        await ctx.channel.send("サーバーエラーが発生しました\nゲームを終了します")
        await uno_end(bot.get_guild(ctx.guild.id), True, False)
    except:
        await ctx.channel.send("何らかのエラーが発生しました\nゲームを終了します")
        await uno_end(bot.get_guild(ctx.guild.id), False, False)
        # エラー内容の出力
        print(traceback.format_exc())


# 参加者全員にメンション
def all_mention(guild):
    global ALL_PLAYER
    return " ".join([guild.get_member(ALL_PLAYER[i]).mention for i in range(len(ALL_PLAYER))])


# 手札を送信する(n: ユーザー指定変数, times: 新たに追加される手札の枚数, send_flag: 追加カードの分を送信するか)
async def send_card(bot, n, times, send_flag):
    global ALL_DATA
    # 前に送ったDMがあるなら削除
    if ALL_DATA[n][2] is not None:
        await ALL_DATA[n][2].delete()
    add_card = uf.deal_card(times)
    ALL_DATA[n][1] = uf.sort_card(ALL_DATA[n][1] + add_card)
    # 手札が1枚以上なら画像を作成/送信
    if ALL_DATA[n][1]:
        mi.make_hand(ALL_DATA[n][1])
        if uf.card_to_string(add_card) == "なし" or not send_flag:
            card_msg = ""
        else:
            card_msg = f"追加カード↓```{uf.card_to_string(uf.sort_card(add_card))}```"
        card_msg += f"現在の手札↓```{uf.card_to_string(ALL_DATA[n][1])}```"
        if len(card_msg) > 2000:
            card_msg = "現在の手札↓```1度に送信できる文字数制限を超過しているため送信できません```"
        ALL_DATA[n][2] = await bot.get_user(ALL_DATA[n][0]).send(card_msg, file=discord.File(mi.HAND_PASS))
        os.remove(mi.HAND_PASS)
    else:
        card_msg = "手札が全て無くなりました"
        ALL_DATA[n][2] = await bot.get_user(ALL_DATA[n][0]).send(card_msg, file=discord.File(mi.BG_PASS))


# UNOの指摘/宣言
async def declaration_uno(bot, ctx):
    global ALL_DATA, DECLARATION_WAIT
    # ケイスケホンダに指摘
    if cs.Honda in ctx.raw_mentions:
        j = uf.search_player(ctx.author.id, ALL_DATA)
        ALL_DATA[j][4] += 2
        await ctx.channel.send(f"{ctx.author.mention} "
                               f"気安く話しかけてきた不敬罪として、次のあなたのターンを2回パスします", delete_after=10)
    # 他プレイヤーへの指摘
    elif len(ctx.raw_mentions) == 1:
        j = uf.search_player(ctx.raw_mentions[0], ALL_DATA)
        if j is not None:
            # UNOフラグが立ってから10秒以上経過
            if ALL_DATA[j][3][0] and (datetime.now() - ALL_DATA[j][3][1]).seconds >= 10:
                ALL_DATA[j][3] = [False, None]
                await ctx.channel.send(f"{bot.get_user(ALL_DATA[j][0]).mention} "
                                       f"UNOと言っていないのでペナルティーで2枚追加されます", delete_after=10)
                await send_card(bot, j, 2, True)
            else:
                if uf.check_win(ALL_DATA[j][1]):
                    msg = "そのユーザーは、既にUNOと宣言済みです"
                else:
                    msg = "そのユーザーは、今はまだUNOの状態ではありません"
                k = uf.search_player(ctx.author.id, ALL_DATA)
                if ALL_DATA[k][4] == 0:
                    ALL_DATA[k][4] += 0.5
                    await ctx.channel.send(f"{ctx.author.mention} {msg}\n"
                                           f"(次自分のターンが来るまでに、もう1度間違うとペナルティーとなります)", delete_after=10)
                elif ALL_DATA[k][4] == 0.5:
                    ALL_DATA[k][4] += 0.5
                    await ctx.channel.send(f"{ctx.author.mention} {msg}\n"
                                           f"指摘間違いペナルティーとして、次のあなたのターンを1回パスします", delete_after=10)
                else:
                    await ctx.channel.send(f"{ctx.author.mention} あなたは現在UNOの指摘は出来ません", delete_after=5)
    # 自分の宣言
    else:
        j = uf.search_player(ctx.author.id, ALL_DATA)
        if DECLARATION_WAIT:
            await ctx.channel.send(f"{ctx.author.mention} UNOの宣言は色の選択後にしてください", delete_after=5)
        # 自分のUNOフラグが立っている場合
        elif ALL_DATA[j][3][0] and not DECLARATION_WAIT:
            ALL_DATA[j][3] = [False, None]
            await ctx.channel.send(f"{all_mention(bot.get_guild(ctx.guild.id))}\n{ctx.author.mention} がUNOを宣言しました")
        # まだ上がれない手札の場合
        elif not uf.check_win(ALL_DATA[j][1]):
            await ctx.channel.send(f"{ctx.author.mention} まだUNOを宣言できる手札ではありません", delete_after=5)
        else:
            await ctx.channel.send(f"{ctx.author.mention} 既にUNOと宣言済みです", delete_after=5)


# 途中参加
async def joining_uno(bot, ctx):
    global ALL_DATA, ALL_PLAYER, INITIAL_NUM, TURN, JOINING_WAIT
    if JOINING_WAIT:
        await ctx.channel.send(f"{ctx.author.mention} もう少し待ってから途中参加してください", delete_after=5)
        return
    ALL_DATA.append([ctx.author.id, [], None, [False, None], 0])
    ALL_PLAYER.append(ctx.author.id)
    TURN = TURN % len(ALL_DATA)
    await ctx.channel.send(f"{all_mention(bot.get_guild(ctx.guild.id))}\n{ctx.author.mention} が途中参加しました")
    try:
        await send_card(bot, -1, INITIAL_NUM, False)
    except FileNotFoundError:
        pass


# UNOゲーム実行処理
async def run_uno(bot, ctx, type):
    # ターンパス時の処理
    async def turn_pass(pass_stc=""):
        if not get_flag and penalty == 0:
            await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} {pass_stc}山札から1枚引いてパスします", delete_after=5)
            await send_card(bot, i, 1, True)
        else:
            await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} {pass_stc}パスします", delete_after=5)

    # 入力を受け付けない条件一覧
    def ng_check(ctx_wait):
        return all([ctx.channel.id == ctx_wait.channel.id, not ctx_wait.author.bot, ctx_wait.content != ""])

    # ng_check + 指定したユーザーしか入力不可
    def user_check(ctx_wait):
        return ng_check(ctx_wait) and ctx_wait.author.id in ALL_PLAYER

    # 既にUNO実行中の場合はゲームを開始しない
    if uf.UNO_start:
        return await ctx.send(f"{ctx.author.mention} 現在プレイ中なので開始出来ません", delete_after=5)

    global ALL_DATA, ALL_PLAYER, INITIAL_NUM, TURN, DECLARATION_WAIT, JOINING_WAIT
    normal_flag, special_flag, mode_str = False, False, ""
    uf.Card = uf.Card_Normal
    mi.AREA_PASS, mi.BG_PASS = mi.AREA_PASS_temp, mi.BG_PASS_temp
    if type.lower() in ["n", "normal"]:
        normal_flag = True
        mode_str = "ノーマルモードで"
    elif type.lower() in ["s", "special"]:
        special_flag = True
        mi.AREA_PASS, mi.BG_PASS = mi.AREA_SP_PASS, mi.BG_SP_PASS
        mode_str = "特殊ルールモードで"
    elif type.lower() in ["f", "free"]:
        special_flag = True
        mi.AREA_PASS, mi.BG_PASS = mi.AREA_FREE_PASS, mi.BG_FREE_PASS
        mode_str = "フリープレイモードで"
    else:
        return await ctx.send(f"{ctx.author.mention} そんなモードはありません", delete_after=5)
    if all([ctx.channel.id != cs.UNO_room, ctx.channel.id != cs.Test_room]) and not special_flag:
        return await ctx.send(f"{ctx.author.mention} ここでは実行できません", delete_after=5)

    uf.UNO_start = True
    guild = bot.get_guild(ctx.guild.id)
    await ctx.send(f"{mode_str}UNOを開始します\n※必ずダイレクトメッセージの送信を許可にしてください\n"
                   "参加する方は `!Join` と入力してください ( `!Drop` で参加取り消し, `!End` で締め切り, `!Cancel` で中止)")
    ALL_PLAYER, start = [ctx.author.id], datetime.now()
    while True:
        try:
            reply = await bot.wait_for('message', check=ng_check, timeout=3600 - (datetime.now() - start).seconds)
            input = jaconv.z2h(reply.content, ascii=True).lower()
        except asyncio.exceptions.TimeoutError:
            await ctx.send(f"締め切らずに一定時間経過したので、自動的にUNOを終了しました\n")
            if normal_flag:
                await ctx.send(f"{ctx.author.mention} 放置ペナルティーとして-100点が与えられました")
                drop_name = guild.get_member(ctx.author.id).display_name
                ur.add_penalty(ctx.author.id, drop_name, [])
            await uno_end(guild, False, False)
            return
        if input in ["!j", "!join"]:
            if reply.author.id not in ALL_PLAYER:
                ALL_PLAYER.append(reply.author.id)
                await ctx.send(f"{reply.author.mention} 参加しました", delete_after=5)
            else:
                await ctx.send(f"{reply.author.mention} 既に参加済みです", delete_after=5)
        elif input in ["!d", "!drop"] and reply.author.id in ALL_PLAYER:
            if reply.author.id == ctx.author.id:
                await ctx.send(f"{reply.author.mention} 開始者は参加を取り消せません", delete_after=5)
            elif len(ALL_PLAYER) >= 2:
                ALL_PLAYER.remove(reply.author.id)
                await ctx.send(f"{reply.author.mention} 参加を取り消しました", delete_after=5)
        elif input in ["!l", "!list"]:
            stc = [f"{i + 1}. {guild.get_member(ALL_PLAYER[i]).display_name}\n" for i in range(len(ALL_PLAYER))]
            await ctx.send(f"```現在の参加者リスト\n{''.join(stc)}```", delete_after=15)
        elif input in ["!e", "!end"] and ALL_PLAYER:
            if ctx.author.id == reply.author.id or role_check_mode(ctx):
                if len(ALL_PLAYER) >= 2 or role_check_admin(ctx) or special_flag:
                    break
                else:
                    await ctx.send(f"{reply.author.mention} 2人以上でないと開始出来ません", delete_after=5)
            else:
                await ctx.send(f"{reply.author.mention} 開始者以外は締め切れません", delete_after=5)
        elif reply.content == "!cancel" and reply.author.id in ALL_PLAYER:
            if ctx.author.id == reply.author.id or role_check_mode(ctx):
                await uno_end(guild, False, False)
                await ctx.send("中止しました")
                return
            else:
                await ctx.send(f"{reply.author.mention} 開始を宣言した人以外は実行できません", delete_after=5)
    stc = [f"{i + 1}. {guild.get_member(ALL_PLAYER[i]).display_name}\n" for i in range(len(ALL_PLAYER))]
    await ctx.send(f"締め切りました```プレイヤーリスト\n\n{''.join(stc)}```")

    if not normal_flag:
        await ctx.send(f"{all_mention(guild)}\n初期手札の枚数を多数決で決定します\n各自希望する枚数を入力してください (制限時間30秒)")
        want_nums, ok_player, ask_start = [], [], datetime.now()
        while True:
            try:
                reply = await bot.wait_for('message', check=ng_check, timeout=30 - (datetime.now() - ask_start).seconds)
                input = jaconv.z2h(reply.content, digit=True)
            except asyncio.exceptions.TimeoutError:
                break
            if reply.author.id not in ALL_PLAYER:
                continue
            elif not input.isdecimal():
                await ctx.send(f"{reply.author.mention} 数字のみで入力してください", delete_after=5)
            elif 2 <= int(input) <= 100:
                if reply.author.id not in ok_player:
                    want_nums.append(int(input))
                    ok_player.append(reply.author.id)
            else:
                await ctx.send(f"{reply.author.mention} 2～100枚以内で指定してください", delete_after=5)
            if len(ok_player) == len(ALL_PLAYER):
                break
        try:
            INITIAL_NUM = collections.Counter(want_nums).most_common()[0][0]
        except IndexError:
            pass
        await ctx.send(f"初期手札を{INITIAL_NUM}枚に設定しました")

        await ctx.send(f"カードの確率設定を変更できます\n"
                       f"テンプレをコピーした後、[]内の数字を変更して送信してください\n変更しない場合は `!No` と入力してください")
        await ctx.send(f"テンプレート↓\n{uf.Card_Template}")
        while True:
            reply = await bot.wait_for('message', check=ng_check)
            input = jaconv.z2h(reply.content, ascii=True, digit=True)
            if reply.author.id not in ALL_PLAYER:
                continue
            elif input.lower() == "!no":
                await ctx.send("カードの確率はデフォルトのままで進行します")
                break
            elif input.count("[") == 0:
                continue
            error = uf.template_check(input)
            if error is None:
                await ctx.send("カードの確率設定を変更しました")
                break
            else:
                await ctx.send(f"{reply.author.mention} 入力エラー\n{error}", delete_after=10)

        await ctx.send(f"カードの色の数を1～4色に変更できます\n数字を入力してください (変更しない場合は4)")
        while True:
            reply = await bot.wait_for('message', check=ng_check)
            input = jaconv.z2h(reply.content, digit=True)
            if reply.author.id not in ALL_PLAYER:
                continue
            elif not input.isdecimal():
                await ctx.send(f"{reply.author.mention} 数字のみで入力してください", delete_after=5)
                continue
            elif not 1 <= int(input) <= 4:
                await ctx.send(f"{reply.author.mention} 1～4色以内で指定してください", delete_after=5)
                continue
            for i in range(4 - int(input)):
                uf.Card = uf.remove_color_card(uf.Color[-1 - i], uf.Card)
            await ctx.send(f"カードの色の数を{input}色に設定しました")
            break
    else:
        await ctx.send(f"ノーマルモードで開始したため、初期手札{INITIAL_NUM}枚、カードの確率はデフォルトとなります")

    random.shuffle(ALL_PLAYER)
    # ALL_DATA == [id, 手札リスト, DM変数, [UNOフラグ, フラグが立った時間], パスペナルティー回数] × 人数分
    ALL_DATA = [[id, [], None, [False, None], 0] for id in ALL_PLAYER]
    msg = await ctx.send("カード配り中...")
    for i in range(len(ALL_PLAYER)):
        try:
            await send_card(bot, i, INITIAL_NUM, False)
        except Forbidden:
            await ctx.send(f"{bot.get_user(ALL_PLAYER[i]).mention} DMの送信を許可していないのでカードが配れません\n"
                           f"許可してから途中参加してください")
            ALL_PLAYER.pop(i)
            ALL_DATA.pop(i)
    await msg.delete()
    stc = [f"{i + 1}. {guild.get_member(ALL_PLAYER[i]).display_name}\n" for i in range(len(ALL_PLAYER))]
    await ctx.send(f"カードを配りました、各自BotからのDMを確認してください\nゲームの進行順は以下のようになります```{''.join(stc)}```")

    await ctx.send(f"{all_mention(guild)}\nゲームを始めてもよろしいですか？(1分以上経過 or 全員が `!OK` で開始)")
    ok_player, ask_start = [], datetime.now()
    while True:
        try:
            reply = await bot.wait_for('message', check=user_check, timeout=60 - (datetime.now() - ask_start).seconds)
        except asyncio.exceptions.TimeoutError:
            break
        if reply.author.id not in ok_player and reply.author.id in ALL_PLAYER:
            if jaconv.z2h(reply.content, ascii=True).lower() == "!ok":
                ok_player.append(reply.author.id)
        if len(ok_player) == len(ALL_PLAYER):
            break
    TURN, card, penalty, winner, msg1, msg2, time_cut = 0, [uf.number_card()], 0, None, None, None, 0
    start_time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M')
    msg_watchgame = None
    shutil.copy(mi.AREA_PASS, mi.AREA_COPY_PASS)
    mi.make_area(card[-1])
    JOINING_WAIT = False

    while True:
        # 観戦機能ON時は手札を表示
        if WATCH_FLAG is not None:
            if msg_watchgame is not None:
                await msg_watchgame.delete()
            msg = ""
            for j in range(len(ALL_DATA)):
                name = f"{j + 1}. {guild.get_member(ALL_DATA[j][0]).display_name}"
                hand = uf.card_to_string(ALL_DATA[j][1])
                if len(name) + len(hand) <= 1970 // len(ALL_PLAYER):
                    msg += f"{name}【{hand}】\n\n"
                else:
                    msg += f"{name}【文字数制限を超過しているため表示できません】\n\n"
            msg_watchgame = await bot.get_channel(WATCH_FLAG).send(f"```\n各プレイヤーの現在の手札一覧\n\n{msg}```")
        # i: ユーザー指定変数, bet_flag: カードを出したか, get_flag: !getでカードを引いたか, drop_flag: 棄権者が出たか
        i, bet_flag, get_flag, drop_flag, bet_card = TURN % len(ALL_DATA), False, False, False, ""
        # 参加者のIDリスト
        ALL_PLAYER = [ALL_DATA[j][0] for j in range(len(ALL_DATA))]
        # 制限時間設定
        time = len(ALL_DATA[i][1]) * 5 + 5
        time = 30 if time < 30 else 60 if time > 60 else time
        time, time_cut = round(time / 4 ** time_cut, 1), 0
        # UNO指摘間違いリセット
        ALL_DATA[i][4] = int(ALL_DATA[i][4])
        # 場札更新の際に以前のメッセージを削除
        if msg1 is not None:
            await msg1.delete()
            await msg2.delete()
        stc = [f"{j + 1}. {guild.get_member(ALL_DATA[j][0]).display_name} : {len(ALL_DATA[j][1])}枚\n"
               for j in range(len(ALL_DATA))]
        msg1 = await ctx.send(f"```\n各プレイヤーの現在の手札枚数\n\n{''.join(stc)}```"
                              f"__現在の場札のカード : {card[-1]}__", file=discord.File(mi.AREA_COPY_PASS))
        msg2 = await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} の番です (制限時間{time:g}秒)")
        # 手札が100枚を超えたら脱落
        if len(ALL_DATA[i][1]) > 100 and special_flag:
            await ctx.send(f"{all_mention(guild)}\n{bot.get_user(ALL_DATA[i][0]).mention} 手札が100枚を超えたので脱落となります")
            if len(ALL_PLAYER) == 1:
                await ctx.send("プレイヤーが0人となったのでゲームを終了しました")
                await uno_end(guild, True, False)
                return
            else:
                ALL_DATA.pop(i)
                continue
        # 記号しか無い時は2枚追加(1度のみ)
        if all([uf.card_to_id(j) % 100 > 9 for j in ALL_DATA[i][1]]):
            await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} 記号残りなので2枚追加します", delete_after=10)
            await send_card(bot, i, 2, True)
        # カード入力処理
        start = datetime.now()
        while True:
            # パスペナルティーが残っている場合
            if ALL_DATA[i][4] >= 1:
                ALL_DATA[i][4] -= 1
                await turn_pass("ペナルティーが課せられているので、このターンは強制的に")
                break
            try:
                reply = await bot.wait_for('message', check=ng_check, timeout=time - (datetime.now() - start).seconds)
                input = jaconv.z2h(jaconv.h2z(reply.content), kana=False, ascii=True, digit=True).lower()
            except asyncio.exceptions.TimeoutError:
                await turn_pass("時間切れとなったので")
                break
            # ゲームから棄権する
            if "!drop" in input and (reply.author.id in ALL_PLAYER or role_check_mode(reply)):
                # 棄権者を指定
                if len(ALL_DATA) > 2 and len(reply.raw_mentions) == 1:
                    if role_check_mode(reply) or special_flag:
                        j = uf.search_player(reply.raw_mentions[0], ALL_DATA)
                        if j is not None:
                            await ctx.send(f"{all_mention(guild)}\n{bot.get_user(ALL_DATA[j][0]).mention} を棄権させました")
                            TURN = i - 1 if j < i else i
                            if normal_flag:
                                drop_name = guild.get_member(ALL_DATA[j][0]).display_name
                                ur.add_penalty(ALL_DATA[j][0], drop_name, ALL_DATA[j][1])
                            ALL_DATA.pop(j)
                            drop_flag = True
                            break
                    else:
                        await ctx.send(f"{reply.author.mention} 棄権させられる権限がありません", delete_after=10)
                # 自分が棄権する
                elif len(ALL_DATA) > 2 and len(reply.raw_mentions) == 0:
                    j = uf.search_player(reply.author.id, ALL_DATA)
                    if j is not None:
                        await ctx.send(f"{all_mention(guild)}\n{reply.author.mention} が棄権しました")
                        TURN = i - 1 if j < i else i
                        if normal_flag:
                            drop_name = guild.get_member(reply.author.id).display_name
                            ur.add_penalty(reply.author.id, drop_name, ALL_DATA[j][1])
                        ALL_DATA.pop(j)
                        drop_flag = True
                        break
                else:
                    await ctx.send(f"{reply.author.mention} 2人以下の状態では棄権出来ません", delete_after=10)
            # ゲームを強制中止する
            elif input == "!cancel" and reply.author.id in ALL_PLAYER:
                await ctx.send(f"{all_mention(guild)}\nゲームを中止しますか？(過半数が `!OK` で中止、`!NG` でキャンセル)")
                TURN_cancel, TURN_ng, cancel_player, ng_player = 0, 0, [], []
                while True:
                    confirm = await bot.wait_for('message', check=user_check)
                    input = jaconv.z2h(confirm.content, ascii=True).lower()
                    if input == "!ok" and confirm.author.id not in cancel_player:
                        TURN_cancel += 1
                        cancel_player.append(confirm.author.id)
                    elif input == "!ng" and confirm.author.id not in ng_player:
                        TURN_ng += 1
                        ng_player.append(confirm.author.id)
                    if TURN_cancel >= len(ALL_PLAYER) // 2 + 1:
                        await uno_end(guild, True, False)
                        await ctx.send(f"{all_mention(guild)}\nゲームを中止しました")
                        return
                    elif TURN_ng >= len(ALL_PLAYER) // 2 + 1:
                        await ctx.send(f"{all_mention(guild)}\nキャンセルしました")
                        break
            # 自分のターンでの行動
            elif reply.author.id == ALL_DATA[i][0] and "!uno" not in input:
                # 山札から1枚引く
                if input in ["!g", "!get"]:
                    if not get_flag:
                        await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} 山札から1枚引きます", delete_after=5)
                        await send_card(bot, i, 1, True)
                        get_flag = True
                    else:
                        await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} 山札から引けるのは1度のみです", delete_after=5)
                # カードを出さない
                elif input in ["!p", "!pass"]:
                    await turn_pass()
                    break
                else:
                    # 出せるカードかチェック
                    bet_card = uf.string_to_card(input)
                    error = uf.check_card(card[-1], bet_card, ALL_DATA[i][1], penalty)
                    if error is None:
                        # 出したカードを山場に追加
                        card += bet_card
                        # 場札更新
                        for j in bet_card:
                            # 出したカードを手札から削除
                            ALL_DATA[i][1].remove(j)
                            # 7が出されたらタイム減少
                            if uf.card_to_id(j) % 100 == 7:
                                time_cut += 1
                        # ドロー/ドボンのペナルティー枚数計算
                        penalty += uf.calculate_penalty(bet_card)
                        bet_flag = True
                        break
                    else:
                        await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} {error}", delete_after=7)
        # 棄権時は以下の処理を飛ばす
        if drop_flag:
            continue
        DECLARATION_WAIT = True
        # ワイルドカード処理(色指定)
        if 500 <= uf.card_to_id(card[-1]) <= 569 and bet_flag:
            msg = await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} 色を指定してください (制限時間20秒)\n"
                                 f"(赤[R] / 青[B] / 緑[G] / 黄[Y] / ランダム[X] と入力)")
            start = datetime.now()
            while True:
                try:
                    color = await bot.wait_for('message', check=user_check,
                                               timeout=20 - (datetime.now() - start).seconds)
                    input = jaconv.z2h(color.content, ascii=True, kana=False).lower()
                except asyncio.exceptions.TimeoutError:
                    await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} 時間切れなのでランダムで決めます", delete_after=10)
                    card[-1] = f"{random.choice(uf.Color)}{card[-1]}"
                    break
                if color.author.id != ALL_DATA[i][0]:
                    continue
                if uf.translate_input(input) not in uf.Color + ["ランダム", "x"]:
                    await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} そんな色はありません", delete_after=5)
                    continue
                if uf.translate_input(input) in uf.Color:
                    card[-1] = f"{uf.translate_input(input)}{card[-1]}"
                else:
                    card[-1] = f"{random.choice(uf.Color)}{card[-1]}"
                break
            bet_card[-1] = card[-1]
            await msg.delete()
        # ディスカードオール処理
        if (uf.card_to_id(card[-1]) % 100 == 13 or 570 <= uf.card_to_id(card[-1]) <= 574) and bet_flag:
            wild_cnt = 0
            for j in range(len(bet_card)):
                if 570 <= uf.card_to_id(bet_card[j]) <= 574:
                    wild_cnt += 1
            if wild_cnt >= 1:
                msg = await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} "
                                     f"消去したい色を{wild_cnt}色指定してください(重複可) (制限時間20秒)\n"
                                     f"(赤[R] / 青[B] / 緑[G] / 黄[Y] / ランダム[X] と入力)")
                start = datetime.now()
                while True:
                    try:
                        color = await bot.wait_for('message', check=user_check,
                                                   timeout=20 - (datetime.now() - start).seconds)
                        input = uf.string_to_card(jaconv.z2h(color.content, ascii=True, kana=False).lower())
                    except asyncio.exceptions.TimeoutError:
                        await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} 時間切れなのでランダムで決めます", delete_after=10)
                        for j in range(-len(bet_card), 0):
                            if 570 <= uf.card_to_id(card[j]) <= 574:
                                card[j] = f"{random.choice(uf.Color)}{card[j]}"
                                bet_card[j] = card[j]
                        break
                    if color.author.id != ALL_DATA[i][0]:
                        continue
                    if not all([uf.translate_input(input[j]) in uf.Color + ["ランダム", "x"] for j in range(len(input))]):
                        await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} 間違った色が含まれています", delete_after=5)
                        continue
                    if len(input) != wild_cnt:
                        await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} 色の数が間違っています", delete_after=5)
                        continue
                    k = 0
                    for j in range(-len(bet_card), 0):
                        if 570 <= uf.card_to_id(card[j]) <= 574:
                            if input[k] in uf.Color:
                                card[j] = f"{uf.translate_input(input[k])}{card[j]}"
                            else:
                                card[j] = f"{random.choice(uf.Color)}{card[j]}"
                            bet_card[j] = card[j]
                            k += 1
                    break
                await msg.delete()
            colors = set([f"{bet_card[j][0]}色" for j in range(len(bet_card))])
            await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} "
                           f"{', '.join(colors)} のカードを全て捨てます", delete_after=10)
            for j in range(len(bet_card)):
                ALL_DATA[i][1] = uf.remove_color_card(bet_card[j][0], ALL_DATA[i][1])
            # 全部カードが無くなった場合
            if not ALL_DATA[i][1]:
                await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} 記号上がりとなるので2枚追加します", delete_after=10)
                await send_card(bot, i, 2, True)
            else:
                await send_card(bot, i, 0, False)
        # ディスカードオール以外の場合の手札更新
        elif bet_flag:
            await send_card(bot, i, 0, False)
        DECLARATION_WAIT = False
        # ペナルティーを受ける
        if penalty > 0 and not bet_flag:
            # ドローの場合
            if 540 <= uf.card_to_id(card[-1]) <= 544 or uf.card_to_id(card[-1]) % 100 == 12:
                await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} ペナルティーで{penalty}枚追加します", delete_after=10)
                await send_card(bot, i, penalty, True)
            # ドボンの場合
            else:
                await ctx.send(f"{all_mention(guild)}\n{bot.get_user(ALL_DATA[i - 1][0]).mention}以外の全員に"
                               f"ペナルティーで{penalty}枚追加します", delete_after=10)
                for j in range(len(ALL_PLAYER)):
                    if ALL_DATA[i - 1][0] != ALL_PLAYER[j]:
                        await send_card(bot, j, penalty, True)
            penalty, TURN, = 0, TURN - 1
        # 手札が0枚となったので上がり
        if not ALL_DATA[i][1] and not ALL_DATA[i][3][0]:
            await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} YOU WIN!")
            winner = i
            break
        # 手札は0枚になったがUNOの宣言忘れ
        elif not ALL_DATA[i][1]:
            await ctx.send(f"{bot.get_user(ALL_DATA[i][0]).mention} UNO宣言忘れのペナルティーで2枚追加します", delete_after=10)
            await send_card(bot, i, 2, True)
        # 上がれる手札になったらUNOフラグを立てる
        elif uf.check_win(ALL_DATA[i][1]):
            ALL_DATA[i][3] = [True, datetime.now()]
        # 上がれない手札だったらUNOフラグを降ろす
        elif not uf.check_win(ALL_DATA[i][1]):
            ALL_DATA[i][3] = [False, None]
        # スキップ処理
        if uf.card_to_id(card[-1]) % 100 == 10 and bet_flag:
            await ctx.send(f"{2 * len(bet_card) - 1}人スキップします", delete_after=10)
            TURN += 2 * len(bet_card) - 1
        # リバース処理
        elif uf.card_to_id(card[-1]) % 100 == 11 and bet_flag:
            await ctx.send(f"{len(bet_card)}回リバースします", delete_after=10)
            if len(bet_card) % 2 == 1:
                # リバースを出した人のリバースされた配列中の位置を代入
                tmp = copy.copy(ALL_DATA[i][0])
                ALL_DATA.reverse()
                TURN = uf.search_player(tmp, ALL_DATA)
        # ワイルドカードで順番シャッフル
        elif 530 <= uf.card_to_id(card[-1]) <= 534 and bet_flag:
            await ctx.send(f"{all_mention(guild)}\n順番がシャッフルされました", delete_after=10)
            random.shuffle(ALL_DATA)
        # 場札更新
        if bet_flag:
            [mi.make_area(j) for j in bet_card]
            # ドロー4 or ドボン1/2 が出された時は画像送信
            if any([540 <= uf.card_to_id(j) <= 544 for j in bet_card]):
                await ctx.send(file=discord.File('src/uno/Draw4_YuGiOh.jpg'), delete_after=30)
            elif 550 <= uf.card_to_id(card[-1]) <= 564:
                await ctx.send(file=discord.File('src/uno/EIKO!_GO!!.png'), delete_after=30)
        # ターンエンド → 次のプレイヤーへ
        TURN += 1

    # 点数計算
    all_name, stc = [], ""
    for i in range(len(ALL_DATA)):
        ALL_DATA[i].append(ur.calculate_point(ALL_DATA[i][1]))
    # 1位には他ユーザーの合計得点をプラス
    ALL_DATA[winner][5] = sum([ALL_DATA[i][5] for i in range(len(ALL_DATA))]) * -1

    # 結果データをソート
    sort_data = sorted(ALL_DATA, key=lambda x: x[5], reverse=True)
    for i in range(len(sort_data)):
        all_name.append(guild.get_member(sort_data[i][0]).display_name)
        last_card = uf.card_to_string(sort_data[i][1])
        if len(last_card) > 1900 // len(ALL_PLAYER) or len(last_card) > 400:
            last_card = "多すぎるため表示出来ません"
        stc += f"{i + 1}位 : {all_name[-1]} ({sort_data[i][5]:+}pts)\n残り手札【{last_card}】\n\n"

    # ゲーム終了処理 (画像やロール削除)
    if normal_flag:
        # 7人以上参加時はWinner/Loserロール付与 & 結果出力
        if 7 <= len(ALL_DATA):
            end_time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%m/%d %H:%M')
            await guild.get_member(sort_data[0][0]).add_roles(get_role(guild, cs.Winner))
            await guild.get_member(sort_data[-1][0]).add_roles(get_role(guild, cs.Loser))
            await bot.get_channel(cs.Result).send(f"__★UNO試合結果 ({start_time} ～ {end_time})__")
            embed = discord.Embed(color=0xff0000)
            embed.set_author(name='Results', icon_url='https://i.imgur.com/F2oH0Bu.png')
            embed.set_thumbnail(url='https://i.imgur.com/JHRshwi.png')
            embed.add_field(name=f"優勝 ({sort_data[0][5]:+}点)", value=f"{all_name[0]}", inline=False)
            for i in range(1, len(sort_data) - 1):
                embed.add_field(name=f"{i + 1}位 ({sort_data[i][5]}点)", value=f"{all_name[i]}")
            embed.add_field(name=f"最下位 ({sort_data[-1][5]}点)", value=f"{all_name[-1]}")
            await bot.get_channel(cs.Result).send(embed=embed)
            role_W, role_L = get_role(guild, cs.Winner), get_role(guild, cs.Loser)
            await bot.get_channel(cs.Result).send(f"{role_W.mention} : {guild.get_member(sort_data[0][0]).mention}\n"
                                                  f"{role_L.mention} : {guild.get_member(sort_data[-1][0]).mention}")
        ur.data_save(sort_data, all_name)
        await ctx.send(f"{all_mention(guild)}```\n★ゲーム結果\n\n{stc}```結果を記録してゲームを終了しました")
        await uno_end(guild, True, True)
    else:
        await ctx.send(f"{all_mention(guild)}```\n★ゲーム結果\n\n{stc}```ゲームを終了しました(結果は反映されません)")
        # フリープレイ時はUNOロールを付与しない
        if mi.AREA_PASS == mi.AREA_SP_PASS:
            await uno_end(guild, True, True)
        else:
            await uno_end(guild, True, False)


# プレイヤーのUNO戦績を表示
async def run_watchgame(ctx):
    global WATCH_FLAG
    if WATCH_FLAG is None:
        WATCH_FLAG = ctx.channel.id
        await ctx.send(f"{ctx.author.mention} UNOの観戦を開始します")
    else:
        WATCH_FLAG = None
        await ctx.send(f"{ctx.author.mention} UNOの観戦を終了します")


# プレイヤーのUNO戦績を表示
async def run_record(bot, guild, ctx, name):
    # UNO会場のみ反応(モデレーター以外)
    if ctx.channel.id != cs.UNO_room and not role_check_mode(ctx):
        return
    if name is None:
        name = guild.get_member(ctx.author.id).display_name
    elif len(re.sub('[^0-9]', "", name)) == 18:
        try:
            name = guild.get_member(int(re.sub('[^0-9]', "", name))).display_name
        except AttributeError:
            pass

    msg = await ctx.send(f"{name}のデータを検索中...")
    for member in get_role(guild, cs.Visitor).members:
        if name.lower() == member.display_name.lower():
            data, player, url, rank = ur.record_output(member.id)
            user, id = member.display_name, member.id
            embed = discord.Embed(title=user, color=0xFF3333)
            embed.set_author(name='UNO Records', icon_url=bot.get_user(id).avatar_url)
            embed.set_thumbnail(url=url)
            embed.add_field(name="順位 (総得点)", value=f"**{data[0]}** /{player}位 ({data[3]:+}点)", inline=False)
            embed.add_field(name="順位 (勝利人数)", value=f"**{rank}** /{player}位 ({data[4]:+}人)", inline=False)
            embed.add_field(name="優勝率", value=f"{data[5]} ({data[7]}回/{data[6]}戦)", inline=False)
            embed.add_field(name="最高獲得点", value=f"{data[9]}点")
            embed.add_field(name="最低減少点", value=f"{data[10]}点")
            embed.add_field(name="直近5戦", value=f"{data[11]}点")
            await ctx.send(embed=embed)
            return await msg.delete()

    await ctx.send(f"{ctx.author.mention} データが記録されていません")
    await msg.delete()
    return


# BotとのDMを全削除
async def run_cleardm(bot, ctx):
    global ALL_PLAYER
    # UNOプレイ中の場合はコマンド実行不可
    if ctx.author.id in ALL_PLAYER:
        return await ctx.send(f"{ctx.author.mention} UNOプレイ中は削除できません", delete_after=5)

    msg = await ctx.send(f"{ctx.author.mention} BotとのDMを削除中...")
    messages = await bot.get_user(ctx.author.id).history(limit=None).flatten()
    for message in messages:
        if message.author.id != ctx.author.id:
            await message.delete()
    await msg.delete()
    await ctx.send(f"{ctx.author.mention} 削除が完了しました", delete_after=5)


class Uno(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener(name='on_message')
    @commands.guild_only()
    @commands.has_role(cs.Visitor)
    async def on_message(self, ctx):
        # UNOプレイ中でない時は反応しない
        if not ALL_DATA:
            return
        if ctx.channel.id not in [cs.UNO_room, cs.Test_room] or ctx.author.bot:
            return

        inputs = jaconv.z2h(jaconv.h2z(ctx.content), kana=False, ascii=True, digit=True).lower()
        if "!uno" in inputs and ctx.author.id in ALL_PLAYER:
            await declaration_uno(self.bot, ctx)
        elif inputs in ["!j", "!join"] and ctx.author.id not in ALL_PLAYER:
            await joining_uno(self.bot, ctx)

    @commands.command()
    async def unorule(self, ctx):
        await ctx.channel.send(f"ルール設定や手札の出し方など↓```{uf.Rule}```")

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def wg(self, ctx):
        await run_watchgame(ctx)

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def watchgame(self, ctx):
        await run_watchgame(ctx)

    @commands.command()
    @commands.guild_only()
    async def us(self, ctx, type="normal"):
        await run_uno_config(self.bot, ctx, type)

    @commands.command()
    @commands.guild_only()
    async def unostart(self, ctx, type="normal"):
        await run_uno_config(self.bot, ctx, type)

    @commands.command()
    @commands.has_role(cs.UNO)
    async def rc(self, ctx, name=None):
        await run_record(self.bot, self.bot.get_guild(ctx.guild.id), ctx, name)

    @commands.command()
    @commands.has_role(cs.UNO)
    async def record(self, ctx, name=None):
        await run_record(self.bot, self.bot.get_guild(ctx.guild.id), ctx, name)

    @commands.command()
    async def cdm(self, ctx):
        await run_cleardm(self.bot, ctx)

    @commands.command()
    async def cleardm(self, ctx):
        await run_cleardm(self.bot, ctx)


def setup(bot):
    return bot.add_cog(Uno(bot))
