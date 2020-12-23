import discord
from discord.ext import commands
from discord.errors import Forbidden, DiscordServerError, HTTPException
import aiohttp.client_exceptions as ac
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
NOW_PLAYING = []


# ゲーム終了処理 (画像やロール削除)
async def uno_end(guild, all_player, image_flag=False, new_flag=False):
    global NOW_PLAYING
    if image_flag:
        os.remove(mi.AREA_COPY_PASS)
    # 新規プレイヤーにはUNOロール付与
    if new_flag:
        for player in all_player:
            if cs.UNO not in [roles.id for roles in guild.get_member(player).roles]:
                await guild.get_member(player).add_roles(get_role(guild, cs.UNO))
    uf.UNO_start = False
    NOW_PLAYING = []


# ゲーム終了処理 (画像やロール削除)
async def run_uno_config(bot, ctx, type):
    try:
        await run_uno(bot, ctx, type)
    except DiscordServerError or ac.ClientOSError:
        await ctx.channel.send("サーバーエラーが発生しました\nゲームを終了します")
        await uno_end(bot.get_guild(ctx.guild.id), [], True, False)
    except:
        await ctx.channel.send("何らかのエラーが発生しました\nゲームを終了します")
        await uno_end(bot.get_guild(ctx.guild.id), [], False, False)
        # エラー内容の出力
        print(traceback.format_exc())


# UNOゲーム実行処理
async def run_uno(bot, ctx, type):
    def all_mention():
        return " ".join([guild.get_member(all_player[i]).mention for i in range(len(all_player))])

    # 手札を送信する(n: ユーザー指定変数, times: 新たに追加される手札の枚数, send_flag: 追加カードの分を送信するか)
    async def send_card(n, times, send_flag):
        # 前に送ったDMがあるなら削除
        if all_data[n][2] is not None:
            await all_data[n][2].delete()
        add_card = uf.deal_card(times)
        all_data[n][1] = uf.sort_card(all_data[n][1] + add_card)
        # 手札が1枚以上なら画像を作成/送信
        if all_data[n][1]:
            mi.make_hand(all_data[n][1])
            if uf.card_to_string(add_card) == "なし" or not send_flag:
                card_msg = ""
            else:
                card_msg = f"追加カード↓```{uf.card_to_string(uf.sort_card(add_card))}```"
            card_msg += f"現在の手札↓```{uf.card_to_string(all_data[n][1])}```"
            if len(card_msg) > 2000:
                card_msg = "現在の手札↓```文字数制限(2000文字)を超過しているため、文字で送信できません```"
            all_data[n][2] = await bot.get_user(all_data[n][0]).send(card_msg, file=discord.File(mi.HAND_PASS))
            os.remove(mi.HAND_PASS)
        else:
            card_msg = "手札が全て無くなりました"
            all_data[n][2] = await bot.get_user(all_data[n][0]).send(card_msg, file=discord.File(mi.BG_PASS))

    # ターンパス時の処理
    async def turn_pass(pass_stc=""):
        if not get_flag and penalty == 0:
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} {pass_stc}山札から1枚引いてパスします", delete_after=5)
            await send_card(i, 1, True)
        else:
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} {pass_stc}パスします", delete_after=5)

    # 入力を受け付けない条件一覧
    def ng_check(ctx_wait):
        return all([ctx.channel.id == ctx_wait.channel.id, not ctx_wait.author.bot, ctx_wait.content != ""])

    # ng_check + 指定したユーザーしか入力不可
    def user_check(ctx_wait):
        return ng_check(ctx_wait) and ctx_wait.author.id in all_player

    # 既にUNO実行中の場合はゲームを開始しない
    if uf.UNO_start:
        return await ctx.send(f"{ctx.author.mention} 現在プレイ中なので開始出来ません", delete_after=5)

    global NOW_PLAYING
    normal_flag, special_flag, mode_str = False, False, ""
    uf.Card = uf.Card_Normal
    mi.AREA_PASS, mi.BG_PASS, mi.CARD_PASS = mi.AREA_PASS_temp, mi.BG_PASS_temp, mi.CARD_PASS_temp
    if type.lower() in ["n", "normal"]:
        normal_flag = True
        mode_str = "ノーマルモードで"
    elif type.lower() in ["s", "special"]:
        special_flag = True
        mi.AREA_PASS, mi.BG_PASS = mi.AREA_SP_PASS, mi.BG_SP_PASS
        mode_str = "特殊ルールモードで"
    elif type.lower() in ["f", "free"]:
        special_flag = True
        mi.AREA_PASS, mi.BG_PASS, mi.CARD_PASS = mi.AREA_FREE_PASS, mi.BG_FREE_PASS, mi.CARD_NORMAL_PASS
        mode_str = "フリープレイモードで"
    else:
        return await ctx.send(f"{ctx.author.mention} そんなモードはありません", delete_after=5)
    if all([ctx.channel.id != cs.UNO_room, ctx.channel.id != cs.Test_room]) and not special_flag:
        return await ctx.send(f"{ctx.author.mention} ここでは実行できません", delete_after=5)

    uf.UNO_start = True
    guild = bot.get_guild(ctx.guild.id)
    await ctx.send(f"{mode_str}UNOを開始します\n※必ずダイレクトメッセージの送信を許可にしてください\n"
                   "参加する方は `!Join` と入力してください ( `!Drop` で参加取り消し, `!End` で締め切り, `!Cancel` で中止)")
    all_player = [ctx.author.id]
    while True:
        reply = await bot.wait_for('message', check=ng_check)
        input = jaconv.z2h(reply.content, ascii=True).lower()
        if input in ["!j", "!join"]:
            if reply.author.id not in all_player:
                all_player.append(reply.author.id)
                await ctx.send(f"{reply.author.mention} 参加しました", delete_after=5)
            else:
                await ctx.send(f"{reply.author.mention} 既に参加済みです", delete_after=5)
        elif input in ["!d", "!drop"] and reply.author.id in all_player:
            if reply.author.id == ctx.author.id:
                await ctx.send(f"{reply.author.mention} 開始者は参加を取り消せません", delete_after=5)
            elif len(all_player) >= 2:
                all_player.remove(reply.author.id)
                await ctx.send(f"{reply.author.mention} 参加を取り消しました", delete_after=5)
        elif input in ["!l", "!list"]:
            stc = [f"{i + 1}. {guild.get_member(all_player[i]).display_name}\n" for i in range(len(all_player))]
            await ctx.send(f"```現在の参加者リスト\n{''.join(stc)}```", delete_after=15)
        elif input in ["!e", "!end"] and all_player:
            if ctx.author.id == reply.author.id or role_check_mode(ctx):
                if len(all_player) >= 2 or role_check_admin(ctx) or special_flag:
                    break
                else:
                    await ctx.send(f"{reply.author.mention} 2人以上でないと開始出来ません", delete_after=5)
            else:
                await ctx.send(f"{reply.author.mention} 開始者以外は締め切れません", delete_after=5)
        elif reply.content == "!cancel" and reply.author.id in all_player:
            if ctx.author.id == reply.author.id or role_check_mode(ctx):
                await uno_end(guild, all_player, False, False)
                await ctx.send("中止しました")
                return
            else:
                await ctx.send(f"{reply.author.mention} 開始を宣言した人以外は実行できません", delete_after=5)
    stc = [f"{i + 1}. {guild.get_member(all_player[i]).display_name}\n" for i in range(len(all_player))]
    await ctx.send(f"締め切りました```プレイヤーリスト\n\n{''.join(stc)}```")

    if not normal_flag:
        await ctx.send(f"{all_mention()}\n初期手札の枚数を多数決で決定します\n各自希望する枚数を入力してください (制限時間30秒)")
        want_nums, ok_player, ask_start = [], [], datetime.now()
        while True:
            try:
                reply = await bot.wait_for('message', check=ng_check, timeout=30 - (datetime.now() - ask_start).seconds)
                input = jaconv.z2h(reply.content, digit=True)
            except asyncio.exceptions.TimeoutError:
                break
            if reply.author.id not in all_player:
                continue
            elif not input.isdecimal():
                await ctx.send(f"{reply.author.mention} 数字のみで入力してください", delete_after=5)
            elif 2 <= int(input) <= 1000:
                if reply.author.id not in ok_player:
                    want_nums.append(int(input))
                    ok_player.append(reply.author.id)
            else:
                await ctx.send(f"{reply.author.mention} 2～1000枚以内で指定してください", delete_after=5)
            if len(ok_player) == len(all_player):
                break
        try:
            initial_num = collections.Counter(want_nums).most_common()[0][0]
        except IndexError:
            initial_num = 7
        await ctx.send(f"初期手札を{initial_num}枚に設定しました")

        await ctx.send(f"カードの確率設定を変更します\n"
                       f"テンプレをコピーした後、[]内の数字を変更して送信してください\n変更しない場合は `!No` と入力してください")
        await ctx.send(f"テンプレート↓\n{uf.Card_Template}")
        while True:
            reply = await bot.wait_for('message', check=ng_check)
            input = jaconv.z2h(reply.content, ascii=True, digit=True)
            if reply.author.id not in all_player:
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
    else:
        initial_num = 7
        await ctx.send(f"ノーマルモードで開始したため、初期手札{initial_num}枚、カードの確率はデフォルトとなります")

    NOW_PLAYING = all_player
    random.shuffle(all_player)
    # all_data == [id, 手札リスト, DM変数, [UNOフラグ, フラグが立った時間]] × 人数分
    all_data = [[id, [], None, [False, None]] for id in all_player]
    msg = await ctx.send("カード配り中...")
    for i in range(len(all_player)):
        try:
            await send_card(i, initial_num, False)
        except Forbidden:
            await ctx.send(f"{bot.get_user(all_player[i]).mention} DMの送信を許可していないのでカードが配れません\n"
                           f"許可してから途中参加してください")
            all_player.pop(i)
            all_data.pop(i)
    await msg.delete()
    stc = [f"{i + 1}. {guild.get_member(all_player[i]).display_name}\n" for i in range(len(all_player))]
    await ctx.send(f"カードを配りました、各自BotからのDMを確認してください\nゲームの進行順は以下のようになります```{''.join(stc)}```")

    await ctx.send(f"{all_mention()}\nゲームを始めてもよろしいですか？(1分以上経過 or 全員が `!OK` で開始)")
    ok_player, ask_start = [], datetime.now()
    while True:
        try:
            reply = await bot.wait_for('message', check=user_check, timeout=60 - (datetime.now() - ask_start).seconds)
        except asyncio.exceptions.TimeoutError:
            break
        if reply.author.id not in ok_player and reply.author.id in all_player:
            if jaconv.z2h(reply.content, ascii=True).lower() == "!ok":
                ok_player.append(reply.author.id)
        if len(ok_player) == len(all_player):
            break
    cnt, card, penalty, winner, msg1, msg2, time_cut = 0, [uf.number_card()], 0, None, None, None, 0
    start_time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M')
    shutil.copy(mi.AREA_PASS, mi.AREA_COPY_PASS)
    mi.make_area(card[-1])

    while True:
        # i: ユーザー指定変数, bet_flag: カードを出したか, get_flag: !getでカードを引いたか, drop_flag: 棄権者が出たか
        i, bet_flag, get_flag, drop_flag, bet_card = cnt % len(all_data), False, False, False, ""
        # 参加者のIDリスト
        all_player = [all_data[j][0] for j in range(len(all_data))]
        # 制限時間設定
        time = len(all_data[i][1]) * 5 + 5
        time = 30 if time < 30 else 60 if time > 60 else time
        time, time_cut = round(time / 3 ** time_cut, 1), 0
        # 場札更新の際に以前のメッセージを削除
        if msg1 is not None:
            await msg1.delete()
            await msg2.delete()
        stc = [f"{j + 1}. {guild.get_member(all_data[j][0]).display_name} : {len(all_data[j][1])}枚\n"
               for j in range(len(all_data))]
        msg1 = await ctx.send(f"```\n各プレイヤーの現在の手札枚数\n\n{''.join(stc)}```"
                              f"__現在の場札のカード : {card[-1]}__", file=discord.File(mi.AREA_COPY_PASS))
        msg2 = await ctx.send(f"{bot.get_user(all_data[i][0]).mention} の番です (制限時間{time:g}秒)")
        # 記号しか無いかチェック
        while True:
            if all([uf.card_to_id(j) % 100 > 9 for j in all_data[i][1]]):
                await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 記号残りなので2枚追加します", delete_after=10)
                await send_card(i, 2, True)
            else:
                break
        # カード入力処理
        start = datetime.now()
        while True:
            try:
                reply = await bot.wait_for('message', check=ng_check, timeout=time - (datetime.now() - start).seconds)
                input = jaconv.z2h(jaconv.h2z(reply.content), kana=False, ascii=True, digit=True).lower()
            except asyncio.exceptions.TimeoutError:
                await turn_pass("時間切れとなったので")
                break
            # UNOの指摘/宣言
            if "!uno" in input and reply.author.id in all_player:
                # 他プレイヤーへの指摘
                if len(reply.raw_mentions) == 1:
                    j = uf.search_player(reply.raw_mentions[0], all_data)
                    if j is not None:
                        # UNOフラグが立ってから10秒以上経過
                        if all_data[j][3][0] and (datetime.now() - all_data[j][3][1]).seconds >= 10:
                            all_data[j][3] = [False, None]
                            await ctx.send(f"{bot.get_user(all_data[j][0]).mention} "
                                           f"UNOと言っていないのでペナルティーで2枚追加されます", delete_after=10)
                            await send_card(j, 2, True)
                        else:
                            await ctx.send(f"{reply.author.mention} "
                                           f"今は、そのユーザーへのUNOの指摘は無効となっています", delete_after=10)
                # 自分の宣言
                else:
                    j = uf.search_player(reply.author.id, all_data)
                    # 自分のUNOフラグが立っている場合
                    if all_data[j][3][0]:
                        all_data[j][3] = [False, None]
                        await ctx.send(f"{all_mention()}\n{reply.author.mention} がUNOを宣言しました")
                    # 手札が2枚以上ある場合
                    elif len(all_data[j][1]) >= 2:
                        await ctx.send(f"{reply.author.mention} まだUNOを宣言できる手札ではありません", delete_after=10)
                    else:
                        await ctx.send(f"{reply.author.mention} 既にUNOと宣言済みです", delete_after=10)
            # 途中参加
            elif input in ["!j", "!join"] and reply.author.id not in all_player:
                all_player.append(reply.author.id)
                all_data.append([reply.author.id, [], None, [False, None]])
                NOW_PLAYING.append(reply.author.id)
                await send_card(-1, initial_num, False)
                await ctx.send(f"{all_mention()}\n{reply.author.mention} が途中参加しました")
                cnt = i
            # ゲームから棄権する
            elif "!drop" in input and reply.author.id in all_player:
                # 棄権者を指定
                if len(all_data) > 2 and len(reply.raw_mentions) == 1:
                    if role_check_mode(reply) or special_flag:
                        j = uf.search_player(reply.raw_mentions[0], all_data)
                        if j is not None:
                            await ctx.send(f"{all_mention()}\n{bot.get_user(all_data[j][0]).mention} を棄権させました")
                            cnt = i - 1 if j < i else i
                            if special_flag:
                                drop_name = guild.get_member(all_data[j][0]).display_name
                                ur.add_penalty(all_data[j][0], drop_name, all_data[j][1])
                            NOW_PLAYING.remove(all_data[j][0])
                            all_data.pop(j)
                            drop_flag = True
                            break
                    else:
                        role_M = get_role(guild, cs.Moderator)
                        await ctx.send(f"{reply.author.mention}  {role_M.mention}でないと棄権させられません")
                # 自分が棄権する
                elif len(all_data) > 2 and len(reply.raw_mentions) == 0:
                    await ctx.send(f"{all_mention()}\n{reply.author.mention} が棄権しました")
                    j = uf.search_player(reply.author.id, all_data)
                    cnt = i - 1 if j < i else i
                    if special_flag:
                        ur.add_penalty(reply.author.id, guild.get_member(reply.author.id).display_name, all_data[j][1])
                    NOW_PLAYING.remove(reply.author.id)
                    all_data.pop(j)
                    drop_flag = True
                    break
                else:
                    await ctx.send(f"{reply.author.mention} 2人以下の状態では棄権出来ません", delete_after=10)
            # ゲームを強制中止する
            elif input == "!cancel" and reply.author.id in all_player:
                await ctx.send(f"{all_mention()}\nゲームを中止しますか？(過半数が `!OK` で中止、`!NG` でキャンセル)")
                cnt_cancel, cnt_ng, cancel_player, ng_player = 0, 0, [], []
                while True:
                    confirm = await bot.wait_for('message', check=user_check)
                    input = jaconv.z2h(confirm.content, ascii=True).lower()
                    if input == "!ok" and confirm.author.id not in cancel_player:
                        cnt_cancel += 1
                        cancel_player.append(confirm.author.id)
                    elif input == "!ng" and confirm.author.id not in ng_player:
                        cnt_ng += 1
                        ng_player.append(confirm.author.id)
                    if cnt_cancel >= len(all_player) // 2 + 1:
                        await uno_end(guild, all_player, True, False)
                        await ctx.send(f"{all_mention()}\nゲームを中止しました")
                        return
                    elif cnt_ng >= len(all_player) // 2 + 1:
                        await ctx.send(f"{all_mention()}\nキャンセルしました")
                        break
            # 自分のターンでの行動
            elif reply.author.id == all_data[i][0]:
                # 山札から1枚引く
                if input in ["!g", "!get"]:
                    if not get_flag:
                        await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 山札から1枚引きます", delete_after=5)
                        await send_card(i, 1, True)
                        get_flag = True
                    else:
                        await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 山札から引けるのは1度のみです", delete_after=5)
                # カードを出さない
                elif input in ["!p", "!pass"]:
                    await turn_pass()
                    break
                else:
                    # 出せるカードかチェック
                    bet_card = uf.string_to_card(input)
                    error = uf.check_card(card[-1], bet_card, all_data[i][1], penalty)
                    if error is None:
                        # 出したカードを山場に追加
                        card += bet_card
                        # 場札更新
                        for j in bet_card:
                            # 出したカードを手札から削除
                            all_data[i][1].remove(j)
                            # 場札更新
                            mi.make_area(j)
                            # 7が出されたらタイム減少
                            if uf.card_to_id(j) % 100 == 7:
                                time_cut += 1
                        # ディスカードオールの場合は後で手札更新
                        if uf.card_to_id(bet_card[0]) % 100 != 13:
                            await send_card(i, 0, False)
                        # ドロー2/4のペナルティー枚数計算
                        penalty += uf.calculate_penalty(bet_card)
                        bet_flag = True
                        break
                    else:
                        await ctx.send(f"{bot.get_user(all_data[i][0]).mention} {error}", delete_after=7)
        # 棄権時は以下の処理を飛ばす
        if drop_flag:
            continue
        # ワイルドカードを出した後の色指定
        if card[-1] in ["ワイルド", "ドロー4"] and bet_flag:
            msg = await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 色を指定してください (制限時間20秒)\n"
                                 f"(赤[R] / 青[B] / 緑[G] / 黄[Y] / ランダム[X] と入力)")
            start = datetime.now()
            while True:
                try:
                    color = await bot.wait_for('message', check=user_check,
                                               timeout=20 - (datetime.now() - start).seconds)
                    input = jaconv.z2h(color.content, ascii=True, kana=False).lower()
                except asyncio.exceptions.TimeoutError:
                    await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 時間切れなのでランダムで決めます", delete_after=10)
                    card[-1] = f"{random.choice(uf.Color)}{card[-1]}"
                    break
                if color.author.id == all_data[i][0] and uf.translate_input(input) in uf.Color:
                    card[-1] = f"{uf.translate_input(input)}{card[-1]}"
                    break
                elif color.author.id == all_data[i][0] and input in ["ランダム", "x", "random"]:
                    card[-1] = f"{random.choice(uf.Color)}{card[-1]}"
                    break
                elif color.author.id == all_data[i][0]:
                    await ctx.send(f"{bot.get_user(all_data[i][0]).mention} そんな色はありません", delete_after=5)
            await msg.delete()
        # ディスカードオール処理
        if card[-1][1:] == "ディスカードオール" and bet_flag:
            colors = set([f"{bet_card[j][0]}色" for j in range(len(bet_card))])
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} "
                           f"{', '.join(colors)} のカードを全て捨てます", delete_after=10)
            for j in range(len(bet_card)):
                all_data[i][1] = uf.remove_color_card(bet_card[j][0], all_data[i][1])
            # 全部カードが無くなった場合
            if not all_data[i][1]:
                await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 記号上がりとなるので2枚追加します", delete_after=10)
                await send_card(i, 2, True)
            else:
                await send_card(i, 0, False)
        # 上がり
        if not all_data[i][1] and not all_data[i][3][0]:
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} YOU WIN!")
            winner = i
            break
        # 手札は0枚になったがUNO宣言忘れ
        elif not all_data[i][1] and all_data[i][3][0]:
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} UNO宣言忘れのペナルティーで2枚追加します", delete_after=10)
            await send_card(i, 2, True)
        # 残り1枚になったらUNOフラグを立てる
        elif len(all_data[i][1]) == 1 and not all_data[i][3][0]:
            all_data[i][3] = [True, datetime.now()]
        # ドロー2/4のペナルティーを受ける
        if penalty > 0 and not bet_flag:
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} ペナルティーで{penalty}枚追加されました", delete_after=10)
            await send_card(i, penalty, True)
            penalty, cnt, = 0, cnt - 1
        # UNOフラグを降ろす
        if len(all_data[i][1]) >= 2 and all_data[i][3][0]:
            all_data[i][3] = [False, None]
        # 観戦機能ON時は手札を表示(5分間)
        if WATCH_FLAG is not None:
            msg = f"{guild.get_member(all_data[i][0]).display_name}【{uf.card_to_string(all_data[i][1])}】"
            if len(msg) > 2000:
                msg = f"{guild.get_member(all_data[i][0]).display_name}【文字数制限を超過しているため表示できません】"
            await bot.get_channel(WATCH_FLAG).send(msg, delete_after=300)
        # スキップ処理
        elif card[-1][1:] == "スキップ" and bet_flag:
            skip_n = len(bet_card)
            await ctx.send(f"{2 * skip_n - 1}人スキップします", delete_after=10)
            cnt += 2 * skip_n - 1
        # リバース処理
        elif card[-1][1:] == "リバース" and bet_flag:
            reverse_n = len(bet_card)
            await ctx.send(f"{reverse_n}回リバースします", delete_after=10)
            if reverse_n % 2 == 1:
                # リバースを出した人のリバースされた配列中の位置を代入
                tmp = copy.copy(all_data[i][0])
                all_data.reverse()
                cnt = uf.search_player(tmp, all_data)
        # ワイルドカードで順番シャッフル
        elif "ワイルド" in card[-1] and bet_flag:
            await ctx.send(f"{all_mention()}\n順番がシャッフルされました", delete_after=10)
            random.shuffle(all_data)
        # ターンエンド → 次のプレイヤーへ
        cnt += 1

    # 点数計算
    all_name, stc = [], ""
    for i in range(len(all_data)):
        all_data[i].append(ur.calculate_point(all_data[i][1]))
    # 1位には他ユーザーの合計得点をプラス
    all_data[winner][4] = sum([all_data[i][4] for i in range(len(all_data))]) * -1
    sort_data = sorted(all_data, key=lambda x: x[4], reverse=True)
    for i in range(len(sort_data)):
        all_name.append(guild.get_member(sort_data[i][0]).display_name)
        stc += f"{i + 1}位 : {all_name[-1]} ({sort_data[i][4]:+}pts)\n残り手札【{uf.card_to_string(sort_data[i][1])}】\n\n"

    # ゲーム終了処理 (画像やロール削除)
    if normal_flag:
        # 10人以上参加 & 初期手札7~10枚の時、Winner/Loserロール付与 & 結果出力
        if 10 <= len(all_data) and 7 <= initial_num <= 10:
            end_time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%m/%d %H:%M')
            await guild.get_member(sort_data[0][0]).add_roles(get_role(guild, cs.Winner))
            await guild.get_member(sort_data[-1][0]).add_roles(get_role(guild, cs.Loser))
            await bot.get_channel(cs.Result).send(f"__★UNO試合結果 ({start_time} ～ {end_time})__")
            embed = discord.Embed(color=0xff0000)
            embed.set_author(name='Results', icon_url='https://i.imgur.com/F2oH0Bu.png')
            embed.set_thumbnail(url='https://i.imgur.com/JHRshwi.png')
            embed.add_field(name=f"優勝 ({sort_data[0][4]:+}点)", value=f"{all_name[0]}", inline=False)
            for i in range(1, len(sort_data) - 1):
                embed.add_field(name=f"{i + 1}位 ({sort_data[i][4]}点)", value=f"{all_name[i]}")
            embed.add_field(name=f"最下位 ({sort_data[-1][4]}点)", value=f"{all_name[-1]}")
            await bot.get_channel(cs.Result).send(embed=embed)
        ur.data_save(sort_data, all_name)
        await ctx.send(f"{all_mention()}```\n★ゲーム結果\n\n{stc}```結果を記録してゲームを終了しました")
        await uno_end(guild, all_player, True, True)
    else:
        await ctx.send(f"{all_mention()}```\n★ゲーム結果\n\n{stc}```ゲームを終了しました(結果は反映されません)")
        # フリープレイ時はUNOロールを付与しない
        if mi.AREA_PASS == mi.AREA_SP_PASS:
            await uno_end(guild, all_player, True, True)
        else:
            await uno_end(guild, all_player, True, False)


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
            data, player, url = ur.record_output(member.id)
            user, id = member.display_name, member.id
            embed = discord.Embed(title=user, color=0xFF3333)
            embed.set_author(name='UNO Records', icon_url=bot.get_user(id).avatar_url)
            embed.set_thumbnail(url=url)
            embed.add_field(name="順位", value=f"**{data[0]}** /{player}位", inline=False)
            embed.add_field(name="総得点", value=f"**{data[3]}**点")
            embed.add_field(name="勝率", value=f"{data[4]} ({data[5]}戦 {data[6]}勝{data[7]}敗)")
            embed.add_field(name="直近5戦", value=f"{data[11]}点")
            embed.add_field(name="最高獲得点", value=f"{data[8]}点")
            embed.add_field(name="最低減少点", value=f"{data[9]}点")
            embed.add_field(name="加点/減点", value=f"{data[10]}点")
            await ctx.send(embed=embed)
            return await msg.delete()

    await ctx.send(f"{ctx.author.mention} データが記録されていません")
    await msg.delete()
    return


# BotとのDMを全削除
async def run_cleardm(bot, ctx):
    # UNOプレイ中の場合はコマンド実行不可
    if ctx.author.id in NOW_PLAYING:
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
    async def us(self, ctx, type="normal"):
        await run_uno_config(self.bot, ctx, type)

    @commands.command()
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
