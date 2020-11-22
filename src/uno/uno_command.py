import discord
from discord.ext import commands
from discord.errors import Forbidden, DiscordServerError
import asyncio
import asyncio.exceptions
import os
import shutil
import copy
import random
import jaconv
from datetime import datetime
import re
import constant as cs
from multi_func import get_role, role_check_admin, role_check_mode
from . import uno_func as uf
from . import make_image as mi
from . import uno_record as ur


# UNOゲーム実行処理
async def run_uno(bot, guild, ctx):
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
            all_data[n][2] = await bot.get_user(all_data[n][0]).send(card_msg, file=discord.File(mi.HAND_PASS))
            os.remove(mi.HAND_PASS)
        else:
            card_msg = "手札が全て無くなりました"
            all_data[n][2] = await bot.get_user(all_data[n][0]).send(card_msg, file=discord.File(mi.BG_PASS))

    # ターンパス時の処理
    async def turn_pass(pass_stc=""):
        if not get_flag and penalty == 0:
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} {pass_stc}山札から1枚引いてパスします", delete_after=5.0)
            await send_card(i, 1, True)
        else:
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} {pass_stc}パスします", delete_after=5.0)

    # 入力を受け付けない条件一覧
    def ng_check(ctx_wait):
        return all([ctx.channel.id == ctx_wait.channel.id, not ctx_wait.author.bot,
                    ctx_wait.content != "", ctx_wait.content not in cs.Commands])

    # ng_check + 指定したユーザーしか入力不可
    def user_check(ctx_wait):
        return ng_check(ctx_wait) and ctx_wait.author.id in all_player

    # 既にUNO実行中はゲームを開始しない
    if all([ctx.channel.id != cs.UNO_room, ctx.channel.id != cs.Test_room]) or uf.UNO_start:
        return

    uf.UNO_start = True
    role_U = get_role(guild, cs.UNO_Player)
    await ctx.send("UNOを開始します\n※必ずダイレクトメッセージの送信を許可にしてください\n"
                   "参加する方は `!Join` と入力してください ( `!End` で締め切り, `!Cancel` で中止)")
    all_player = []
    while True:
        reply = await bot.wait_for('message', check=ng_check)
        input = jaconv.z2h(reply.content, ascii=True).lower()
        if input in ["!j", "!join"] and reply.author.id not in all_player:
            all_player.append(reply.author.id)
            await guild.get_member(reply.author.id).add_roles(role_U)
            await ctx.send(f"{reply.author.mention} 参加しました", delete_after=5.0)
        elif input in ["!l", "!list"]:
            stc = [f"{i + 1}. {guild.get_member(all_player[i]).display_name}\n" for i in range(len(all_player))]
            await ctx.send(f"```現在の参加者リスト\n{''.join(stc)}```", delete_after=10.0)
        elif input in ["!e", "!end"] and all_player:
            if ctx.author.id == reply.author.id:
                if len(all_player) >= 2 or role_check_admin(ctx):
                    break
                else:
                    await ctx.send(f"{reply.author.mention} 2人以上でないと開始出来ません", delete_after=5.0)
            else:
                await ctx.send(f"{reply.author.mention} 開始を宣言した人以外は実行できません", delete_after=5.0)
        elif reply.content == "!cancel":
            if ctx.author.id == reply.author.id:
                await ctx.send("中止しました")
                uf.UNO_start = False
                return
            else:
                await ctx.send(f"{reply.author.mention} 開始を宣言した人以外は実行できません", delete_after=5.0)
    stc = [f"{i + 1}. {guild.get_member(all_player[i]).display_name}\n" for i in range(len(all_player))]

    await ctx.send(f"```プレイヤーリスト\n\n{''.join(stc)}```締め切りました\n{ctx.author.mention} 初期手札の枚数を入力してください")
    while True:
        reply = await bot.wait_for('message', check=ng_check)
        input = jaconv.z2h(reply.content, digit=True).lower()
        try:
            num = int(re.sub(r'[^0-9]', "", input))
            if ctx.author.id == reply.author.id:
                if 2 <= num <= 100:
                    await ctx.send(f"初期手札を{num}枚で設定しました")
                    break
                else:
                    await ctx.send(f"2～100枚以内で指定してください", delete_after=5.0)
            else:
                await ctx.send(f"{reply.author.mention} あなたには聞いていません", delete_after=5.0)
        except ValueError:
            pass

    await ctx.send(f"ルール設定や手札の出し方など↓```{uf.Rule}```")
    random.shuffle(all_player)
    # all_data == [id, 手札リスト, DM変数, [UNOフラグ, フラグが立った時間]] × 人数分
    all_data = [[id, [], None, [False, None]] for id in all_player]
    for i in range(len(all_player)):
        try:
            await send_card(i, num, False)
        except Forbidden:
            await ctx.send(f"{bot.get_user(all_player[i]).mention} DMの送信を許可していないのでカードが配れません\n"
                           f"許可してから途中参加してください")
            await guild.get_member(all_player[i]).remove_roles(role_U)
            all_player.pop(i)
            all_data.pop(i)
    stc = [f"{i + 1}. {guild.get_member(all_player[i]).display_name}\n" for i in range(len(all_player))]
    await ctx.send(f"カードを配りました、各自BotからのDMを確認してください\nゲームの進行順は以下のようになります```{''.join(stc)}```")

    await ctx.send(f"{role_U.mention} ゲームを始めてもよろしいですか？(1分以上経過 or 全員が `!OK` で開始)")
    cnt_ok, ok_player, ok_start = 0, [], datetime.now()
    while True:
        try:
            reply = await bot.wait_for('message', check=user_check, timeout=60.0 - (datetime.now() - ok_start).seconds)
        except asyncio.exceptions.TimeoutError:
            break
        if reply.author.id not in ok_player:
            if jaconv.z2h(reply.content, ascii=True).lower() == "!ok":
                cnt_ok += 1
                ok_player.append(reply.author.id)
        if cnt_ok == len(all_player):
            break
    cnt, card, penalty, winner, msg1, msg2, time_cut = 0, uf.first_card(), 0, None, None, None, 1
    shutil.copy(mi.AREA_PASS, mi.AREA_TEMP_PASS)
    mi.make_area(card[-1])

    while True:
        # i: ユーザー指定変数, bet_flag: カードを出したか, get_flag: !getでカードを引いたか, drop_flag: 棄権者が出たか
        i, bet_flag, get_flag, drop_flag = cnt % len(all_data), False, False, False
        # 参加者のIDリスト
        all_player = [all_data[j][0] for j in range(len(all_data))]
        # 制限時間設定
        time = len(all_data[i][1]) * 5 + 5
        time = 30 if time < 30 else 60 if time > 60 else time
        time, time_cut = round(time / time_cut, 1), 1
        # 場札更新の際に以前のメッセージを削除
        if msg1 is not None:
            await msg1.delete()
            await msg2.delete()
        stc = [f"{j + 1}. {guild.get_member(all_data[j][0]).display_name} : {len(all_data[j][1])}枚\n"
               for j in range(len(all_data))]
        msg1 = await ctx.send(f"```\n各プレイヤーの現在の手札枚数\n\n{''.join(stc)}```"
                              f"__現在の場札のカード : {card[-1]}__", file=discord.File(mi.AREA_TEMP_PASS))
        msg2 = await ctx.send(f"{bot.get_user(all_data[i][0]).mention} の番です (制限時間{time:g}秒)")
        # 記号しか無いかチェック
        while True:
            if all([uf.card_to_id(j) % 100 > 9 for j in all_data[i][1]]):
                await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 記号残りなので2枚追加されます", delete_after=10.0)
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
                                           f"UNOと言っていないのでペナルティーで2枚追加されます", delete_after=10.0)
                            await send_card(j, 2, True)
                        else:
                            await ctx.send(f"{reply.author.mention} "
                                           f"今は、そのユーザーへのUNOの指摘は無効となっています", delete_after=10.0)
                # 自分の宣言
                else:
                    j = uf.search_player(reply.author.id, all_data)
                    # 自分のUNOフラグが立っている場合
                    if all_data[j][3][0]:
                        all_data[j][3] = [False, None]
                        await ctx.send(f"{role_U.mention}  {reply.author.mention}がUNOを宣言しました")
                    # 手札が2枚以上ある場合
                    elif len(all_data[j][1]) >= 2:
                        await ctx.send(f"{reply.author.mention} 今はUNOを宣言しても意味がありません")
                    else:
                        await ctx.send(f"{reply.author.mention} 既にUNOと宣言済みです")
            # 途中参加
            elif input in ["!j", "!join"] and reply.author.id not in all_player:
                all_player.append(reply.author.id)
                all_data.append([reply.author.id, [], None, [False, None]])
                await send_card(-1, num, False)
                await guild.get_member(reply.author.id).add_roles(role_U)
                await ctx.send(f"{role_U.mention}  {reply.author.mention}が途中参加しました")
                cnt = i
            # ゲームから棄権する
            elif "!drop" in input and reply.author.id in all_player:
                # 棄権者を指定
                if len(all_data) > 2 and len(reply.raw_mentions) == 1 and role_check_mode(reply):
                    j = uf.search_player(reply.raw_mentions[0], all_data)
                    if j is not None:
                        await guild.get_member(all_data[j][0]).remove_roles(role_U)
                        await ctx.send(f"{role_U.mention}  "
                                       f"{bot.get_user(all_data[j][0]).mention}を棄権させました")
                        cnt = i - 1 if j < i else i
                        ur.add_penalty(all_data[j][0], guild.get_member(all_data[j][0]).display_name, all_data[j][1])
                        all_data.pop(j)
                        drop_flag = True
                        break
                    else:
                        await ctx.send(f"{reply.author.mention} そのユーザーはゲームに参加していません", delete_after=5.0)
                # 自分が棄権する
                elif len(all_data) > 2 and len(reply.raw_mentions) == 0:
                    await guild.get_member(reply.author.id).remove_roles(role_U)
                    await ctx.send(f"{role_U.mention}  {reply.author.mention}が棄権しました")
                    j = uf.search_player(reply.author.id, all_data)
                    cnt = i - 1 if j < i else i
                    ur.add_penalty(all_data[j][0], guild.get_member(all_data[j][0]).display_name, all_data[j][1])
                    all_data.pop(j)
                    drop_flag = True
                    break
                else:
                    await ctx.send(f"{reply.author.mention} "
                                   f"2人以下の状態では棄権出来ません(`!Cancel` で中止)", delete_after=5.0)
            # ゲームを強制中止する
            elif input == "!cancel" and reply.author.id in all_player:
                await ctx.send(f"{role_U.mention} ゲームを中止しますか？(過半数が `!OK` で中止、`!NG` でキャンセル)")
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
                        os.remove(mi.AREA_TEMP_PASS)
                        for member in role_U.members:
                            await member.remove_roles(role_U)
                        uf.UNO_start = False
                        await ctx.send(f"{role_U.mention} ゲームを中止しました")
                        return
                    elif cnt_ng >= len(all_player) // 2 + 1:
                        await ctx.send(f"{role_U.mention} キャンセルしました")
                        break
            # 自分のターンでの行動
            elif reply.author.id == all_data[i][0]:
                # 山札から1枚引く
                if input in ["!g", "!get"]:
                    if not get_flag:
                        await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 山札から1枚引きます", delete_after=5.0)
                        await send_card(i, 1, True)
                        get_flag = True
                    else:
                        await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 山札から引けるのは1度のみです", delete_after=5.0)
                # カードを出さない
                elif input in ["!p", "!pass"]:
                    await turn_pass()
                    break
                else:
                    # 出せるカードかチェック
                    check, error = uf.check_card(
                        card[-1], uf.string_to_card(input), all_data[i][1], penalty)
                    if check:
                        # 出したカードを山場に追加
                        bet_card = uf.string_to_card(input)
                        card += bet_card
                        # 場札 & 手札更新(送信)
                        for j in bet_card:
                            # 出したカードを手札から削除
                            all_data[i][1].remove(j)
                            # 場札更新
                            mi.make_area(j)
                            # 7が出されたらタイム減少
                            if uf.card_to_id(j) % 100 == 7:
                                time_cut += 1
                        await send_card(i, 0, True)
                        # ドロー2/4のペナルティー枚数計算
                        penalty += uf.calculate_penalty(uf.string_to_card(input))
                        bet_flag = True
                        break
                    else:
                        await ctx.send(f"{bot.get_user(all_data[i][0]).mention} {error}", delete_after=5.0)
        # 棄権時は以下の処理を飛ばす
        if drop_flag:
            continue
        # ワイルドカードを出した後の色指定
        if card[-1] in ["ワイルド", "ドロー4"] and bet_flag:
            msg = await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 色を指定してください (制限時間20秒)\n"
                                 f"(赤[R] / 青[B] / 緑[G] / 黄[Y] / ランダム[RD] と入力)")
            start = datetime.now()
            while True:
                try:
                    color = await bot.wait_for('message', check=user_check,
                                               timeout=20.0 - (datetime.now() - start).seconds)
                    input = jaconv.z2h(color.content, ascii=True, kana=False).lower()
                except asyncio.exceptions.TimeoutError:
                    await ctx.send(f"{bot.get_user(all_data[i][0]).mention} 時間切れなのでランダムで決めます",
                                   delete_after=10.0)
                    card[-1] = f"{random.choice(uf.Color)}{card[-1]}"
                    break
                if color.author.id == all_data[i][0] and uf.translate_input(input) in uf.Color:
                    card[-1] = f"{uf.translate_input(input)}{card[-1]}"
                    break
                elif color.author.id == all_data[i][0] and input in ["ランダム", "rd", "random"]:
                    card[-1] = f"{random.choice(uf.Color)}{card[-1]}"
                    break
                elif color.author.id == all_data[i][0]:
                    await ctx.send(f"{bot.get_user(all_data[i][0]).mention} そんな色はありません", delete_after=5.0)
            await msg.delete()
        # 上がり
        if not all_data[i][1] and not all_data[i][3][0]:
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} YOU WIN!")
            # 10人以上参加時の勝者にはWinnerロール付与
            if len(all_data) >= 10:
                await guild.get_member(all_data[i][0]).add_roles(get_role(guild, cs.Winner))
            winner = i
            break
        # 手札は0枚になったがUNO宣言忘れ
        elif not all_data[i][1] and all_data[i][3][0]:
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} UNO宣言忘れのペナルティーで2枚追加します", delete_after=10.0)
            await send_card(i, 2, True)
        # 残り1枚になったらUNOフラグを立てる
        elif len(all_data[i][1]) == 1 and not all_data[i][3][0]:
            all_data[i][3] = [True, datetime.now()]
        # ドロー2/4のペナルティーを受ける
        if penalty > 0 and not bet_flag:
            await ctx.send(f"{bot.get_user(all_data[i][0]).mention} ペナルティーで{penalty}枚追加されました", delete_after=10.0)
            await send_card(i, penalty, True)
            penalty, cnt, = 0, cnt - 1
        # UNOフラグを降ろす
        if len(all_data[i][1]) >= 2 and all_data[i][3][0]:
            all_data[i][3] = [False, None]
        # スキップ処理
        elif card[-1][1:] == "スキップ" and bet_flag:
            skip_n = len(uf.string_to_card(input))
            await ctx.send(f"{2 * skip_n - 1}人スキップします", delete_after=10.0)
            cnt += 2 * skip_n - 1
        # リバース処理
        elif card[-1][1:] == "リバース" and bet_flag:
            reverse_n = len(uf.string_to_card(input))
            await ctx.send(f"{reverse_n}回リバースします", delete_after=10.0)
            if reverse_n % 2 == 1:
                # リバースを出した人のリバースされた配列中の位置を代入
                tmp = copy.copy(all_data[i][0])
                all_data.reverse()
                cnt = uf.search_player(tmp, all_data)
        # ワイルドカードで順番シャッフル
        elif "ワイルド" in card[-1] and bet_flag:
            await ctx.send(f"{role_U.mention} 順番がシャッフルされました", delete_after=10.0)
            random.shuffle(all_data)
        cnt += 1

    # 点数計算
    all_pts, all_name, stc = [], [], ""
    for i in range(len(all_data)):
        pts = ur.calculate_point(all_data[i][1])
        all_data[i].append(pts)
        all_pts.append(pts)
    # 1位には他ユーザーの合計得点をプラス
    all_data[winner][4] = sum(all_pts) * -1
    sort_data = sorted(all_data, key=lambda x: x[4], reverse=True)
    for i in range(len(sort_data)):
        all_name.append(guild.get_member(sort_data[i][0]).display_name)
        stc += f"{i + 1}位 : {all_name[-1]} ({sort_data[i][4]}pts)\n"
        stc += f"残り手札【{uf.card_to_string(sort_data[i][1])}】\n\n"
    await ctx.send(f"```\n★ゲーム結果\n\n{stc}```{role_U.mention} 結果を記録してゲームを終了しました")
    ur.data_save(sort_data, all_name)
    os.remove(mi.AREA_TEMP_PASS)
    for member in role_U.members:
        await member.remove_roles(role_U)
    uf.UNO_start = False


# プレイヤーのUNO戦績を表示
async def run_record(bot, guild, ctx, name):
    # UNO会場のみ反応(モデレーター以外)
    if ctx.channel.id != cs.UNO_room and not role_check_mode(ctx):
        return
    if name is None:
        name = guild.get_member(ctx.author.id).display_name

    msg = await ctx.send(f"{name}のデータを検索中...")
    data, url, user, id = [], None, None, None
    for member in get_role(guild, cs.Visitor).members:
        if name.lower() == member.display_name.lower():
            data, url = ur.record_output(member.id)
            user, id = member.display_name, member.id
    if any([data is None, user is None, id is None]):
        await ctx.send(f"{ctx.author.mention} データが記録されていません")
        await msg.delete()
        return
    embed = discord.Embed(title=user, color=0xFF3333)
    embed.set_author(name='UNO Records', icon_url=bot.get_user(id).avatar_url)
    embed.set_thumbnail(url=url)
    embed.add_field(name="総得点", value=f"{data[3]}点")
    embed.add_field(name="勝率", value=f"{data[4]} ({data[5]}戦 {data[6]}勝{data[7]}敗)")
    embed.add_field(name="直近5戦", value=f"{data[11]}点")
    embed.add_field(name="最高獲得点", value=f"{data[8]}点")
    embed.add_field(name="最低減少点", value=f"{data[9]}点")
    embed.add_field(name="ペナルティー", value=f"{data[10]}点")
    await ctx.send(embed=embed)
    await msg.delete()


# BotとのDMを全削除
async def run_cleardm(bot, ctx):
    if ctx.channel.id != cs.UNO_room and ctx.channel.id != cs.Test_room:
        return

    try:
        msg = await ctx.send(f"{ctx.author.mention} BotとのDMを削除中...")
        messages = await bot.get_user(ctx.author.id).history(limit=None).flatten()
        for message in messages:
            if message.author.id != ctx.author.id:
                await message.delete()
        await msg.delete()
        await ctx.send(f"{ctx.author.mention} 削除が完了しました")
    except Forbidden:
        await ctx.send(f"{ctx.author.mention} DMが開放されていないので削除できません")


class Uno(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # サーバーエラー
    @commands.Cog.listener(name='on_command_error')
    @commands.guild_only()
    async def on_command_error(self, ctx, error):
        if isinstance(error, DiscordServerError):
            return await ctx.channel.send("サーバーエラーが発生しました")

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def us(self, ctx):
        await run_uno(self.bot, self.bot.get_guild(cs.Server), ctx)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def unostart(self, ctx):
        await run_uno(self.bot, self.bot.get_guild(cs.Server), ctx)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def rc(self, ctx, name=None):
        await run_record(self.bot, self.bot.get_guild(cs.Server), ctx, name)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def record(self, ctx, name=None):
        await run_record(self.bot, self.bot.get_guild(cs.Server), ctx, name)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def cdm(self, ctx):
        await run_cleardm(self.bot, ctx)

    @commands.command()
    @commands.has_role(cs.Visitor)
    async def cleardm(self, ctx):
        await run_cleardm(self.bot, ctx)


def setup(bot):
    return bot.add_cog(Uno(bot))
