import random
import json
from operator import itemgetter
import constant

File_backup = None
Former_winner = []
Former_loser = []
RECORD_PASS = 'src/zyanken/zyanken_record.json'
REPLY_PASS = 'src/zyanken/no_reply_user.txt'

with open(RECORD_PASS, 'r') as f:
    ZData = json.load(f)
with open(REPLY_PASS, 'r') as f:
    No_reply = f.read().splitlines()


def honda_word(win):
    if win:
        per_word = random.randint(101, 102)
    else:
        per_word = random.randint(1, 9)

    if per_word == 1:
        return "YOU LOSE 俺の勝ち！\nそれで勝てると思ってるんやったら俺がずっと勝ちますよ！"
    elif per_word == 2:
        return "YOU LOSE 俺の勝ち！\n何事も準備がすべて\tそれを怠っている事がバレてますよ"
    elif per_word == 3:
        return "YOU LOSE 俺の勝ち！\nその程度の気持ちで勝てるとでも思ったんですか？ちゃんと練習してきてください"
    elif per_word == 4:
        return "YOU LOSE 俺の勝ち！\nたかがじゃんけん、そう思ってないですか？\tそれやったら明日も、俺が勝ちますよ"
    elif per_word == 5:
        return "YOU LOSE 俺の勝ち！\n負けは次につながるチャンスです！ネバーギブアップ！"
    elif per_word == 6:
        return "YOU LOSE 俺の勝ち！\nなんで負けたか、明日まで考えといてください。そしたら何かが見えてくるはずです"
    elif per_word == 7:
        return "YOU LOSE 俺の勝ち！\n1年間何やってたんですか？この結果はじゃんけんに対する意識の差です"
    elif per_word == 8:
        return "YOU LOSE 俺の勝ち！\nここは練習ではありません\t全身全霊で俺と向き合ってください"
    elif per_word == 9:
        return "YOU LOSE 俺の勝ち！\nあなたの考えてる事ぐらい俺にはお見通しです"
    elif per_word == 101:
        return "YOU WIN\nやるやん。明日は俺にリベンジさせて。"
    elif per_word == 102:
        return "YOU WIN 俺の負け！\n今日は負けを認めます\tただ勝ち逃げは許しませんよ"


def hiragana_to_alpha(hand):
    if hand == "グー":
        return "r"
    elif hand == "チョキ":
        return "s"
    else:
        return "p"


def honda_to_zyanken(my_hand, user):
    if random.randint(1, 2) == 1:  # 勝率95%
        win = True
        img_pass = 'src/zyanken/image/YOU WIN.jpg'
        emoji2 = "🎉"
    else:
        win = False
        img_pass = 'src/zyanken/image/YOU LOSE.jpg'
        emoji2 = "👎"

    if my_hand == "グー":
        if win:
            honda_hand = "チョキ"
            emoji1 = "✌"
        else:
            honda_hand = "パー"
            emoji1 = "✋"
    elif my_hand == "チョキ":
        if win:
            honda_hand = "パー"
            emoji1 = "✋"
        else:
            honda_hand = "グー"
            emoji1 = "✊"
    else:  # my_hand == "パー"
        if win:
            honda_hand = "グー"
            emoji1 = "✊"
        else:
            honda_hand = "チョキ"
            emoji1 = "✌"

    if str(user) not in ZData:
        ZData[str(user)] = {"win": {"r": 0, "s": 0, "p": 0}, "lose": {"r": 0, "s": 0, "p": 0},
                            "keep": {"cnt": 0, "max": 0}}
    if win:
        ZData[str(user)]["win"][hiragana_to_alpha(my_hand)] += 1
        ZData[str(user)]["keep"]["cnt"] += 1
        if ZData[str(user)]["keep"]["cnt"] > ZData[str(user)]["keep"]["max"]:
            ZData[str(user)]["keep"]["max"] = ZData[str(user)]["keep"]["cnt"]
        ZData[str(constant.Honda)]["lose"][hiragana_to_alpha(honda_hand)] += 1
        ZData[str(constant.Honda)]["keep"]["cnt"] = 0
    else:
        ZData[str(user)]["lose"][hiragana_to_alpha(my_hand)] += 1
        ZData[str(user)]["keep"]["cnt"] = 0
        ZData[str(constant.Honda)]["win"][hiragana_to_alpha(honda_hand)] += 1
        ZData[str(constant.Honda)]["keep"]["cnt"] += 1
        if ZData[str(constant.Honda)]["keep"]["cnt"] > ZData[str(constant.Honda)]["keep"]["max"]:
            ZData[str(constant.Honda)]["keep"]["max"] = ZData[str(constant.Honda)]["keep"]["cnt"]

    return img_pass, honda_hand, honda_word(win), emoji1, emoji2


def stats_output(id):
    cnt_win, cnt_lose = 0, 0
    win_data = list(ZData[str(id)]["win"].values())
    lose_data = list(ZData[str(id)]["lose"].values())
    keepwin_data = list(ZData[str(id)]["keep"].values())
    for i in range(3):
        cnt_win += win_data[i]
    for i in range(3):
        cnt_lose += lose_data[i]

    win_rate = cnt_win / (cnt_win + cnt_lose) * 100
    if win_rate <= 50:
        url = 'https://i.imgur.com/adtGl7h.png'  # YOU LOSE
    else:
        url = 'https://i.imgur.com/1JXc9eD.png'  # YOU WIN

    return [cnt_win, cnt_lose, round(win_rate, 2), win_data, lose_data, keepwin_data, url]


def ranking_output(guild, type):
    user = list(ZData.keys())
    users_data = []
    for i in range(len(user)):
        cnt_win = sum(ZData[user[i]]["win"].values())
        cnt_lose = sum(ZData[user[i]]["lose"].values())
        cnt_keepwin = ZData[user[i]]["keep"]["cnt"]
        cnt_maxwin = ZData[user[i]]["keep"]["max"]
        cnt = cnt_win + cnt_lose
        users_data.append([int(user[i]), cnt_win, cnt_lose, (cnt_win / cnt) * 100, cnt_keepwin, cnt_maxwin])

    stc = ""
    if type == "winsmax":
        sort_data = sorted(users_data, key=itemgetter(5, 3), reverse=True)  # 最大勝利数→勝率でソート
        i = 0
        while i < len(sort_data):
            if sort_data[i][1] + sort_data[i][2] < 10:  # 10戦以上
                sort_data.remove(sort_data[i])
                i -= 1
            i += 1

        num = len(sort_data)
        j, k, winner, loser = 1, 0, [], []
        for i in range(num):
            stc += f"{j}位 : {guild.get_member(sort_data[i][0]).display_name} " \
                   f"(最大{sort_data[i][5]}連勝, 勝率{sort_data[i][3]:.02f}%)"
            if (j == 1 or j == 2 or j % 7 == 0) and j != num - 1:  # Winner
                stc += " [Winner]"
                winner.append(sort_data[i][0])
            elif j % 7 != 0 and (j % 6 == 0 or j == num):  # Loser
                stc += " [Loser]"
                loser.append(sort_data[i][0])
            stc += "\n"
            j, k = j + 1 + k, 0
            """
            if i != num - 1:
                if sort_data[i][3] == sort_data[i + 1][3]:  # 同率の場合
                    k += 1
                else:
                    j, k = j + 1 + k, 0
            """
        return "最大連勝数基準(>勝率>登録順), 10戦以上", stc, winner, loser

    else:  # if type == "winsmaxall":
        sort_data = sorted(users_data, key=itemgetter(5, 3), reverse=True)  # ポイント→勝率でソート

        for i in range(len(sort_data)):
            stc += f"{i + 1}位 : {guild.get_member(sort_data[i][0]).display_name} " \
                   f"(最大{sort_data[i][5]}連勝, 勝率{sort_data[i][3]:.02f}%)\n"
        return "最大連勝数基準(>勝率>登録順)", stc, None, None
