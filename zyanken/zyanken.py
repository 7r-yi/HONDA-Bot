import random
import json
from operator import itemgetter
import constant

File_backup = None
Former_loser_point = None
Former_loser_pointall = None

with open('zyanken/zyanken_record.json', 'r') as f:
    Zyanken_data = json.load(f)
with open('zyanken/no_reply_user.txt', 'r') as f:
    No_reply = f.readlines()
with open('zyanken/no_data_user.json', 'r') as f:
    Rm_user = json.load(f)


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
    if random.randint(1, 100) >= 6:  # 勝率95%
        win = True
        img_pass = './zyanken/image/YOU WIN.jpg'
        emoji2 = "🎉"
    else:
        win = False
        img_pass = './zyanken/image/YOU LOSE.jpg'
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

    if str(user) not in Rm_user:  # 過去に退出したことがあるユーザーは記録しない
        if str(user) not in Zyanken_data:
            Zyanken_data[str(user)] = {"win": {"r": 0, "s": 0, "p": 0}, "lose": {"r": 0, "s": 0, "p": 0},
                                       "keep": {"cnt": 0, "max": 0}}
        if win:
            Zyanken_data[str(user)]["win"][hiragana_to_alpha(my_hand)] += 1
            Zyanken_data[str(user)]["keep"]["cnt"] += 1
            if Zyanken_data[str(user)]["keep"]["cnt"] > Zyanken_data[str(user)]["keep"]["max"]:
                Zyanken_data[str(user)]["keep"]["max"] = Zyanken_data[str(user)]["keep"]["cnt"]
            Zyanken_data[str(constant.Honda)]["lose"][hiragana_to_alpha(honda_hand)] += 1
            Zyanken_data[str(constant.Honda)]["keep"]["cnt"] = 0
        else:
            Zyanken_data[str(user)]["lose"][hiragana_to_alpha(my_hand)] += 1
            Zyanken_data[str(user)]["keep"]["cnt"] = 0
            Zyanken_data[str(constant.Honda)]["win"][hiragana_to_alpha(honda_hand)] += 1
            Zyanken_data[str(constant.Honda)]["keep"]["cnt"] += 1
            if Zyanken_data[str(constant.Honda)]["keep"]["cnt"] > Zyanken_data[str(constant.Honda)]["keep"]["max"]:
                Zyanken_data[str(constant.Honda)]["keep"]["max"] = Zyanken_data[str(constant.Honda)]["keep"]["cnt"]

    return img_pass, honda_hand, honda_word(win), emoji1, emoji2


def stats_output(id):
    cnt_win, cnt_lose = 0, 0
    win_data = list(Zyanken_data[str(id)]["win"].values())
    lose_data = list(Zyanken_data[str(id)]["lose"].values())
    keepwin_data = list(Zyanken_data[str(id)]["keep"].values())
    for i in range(3):
        cnt_win += win_data[i]
    for i in range(3):
        cnt_lose += lose_data[i]

    pts = keepwin_data[0] * 3 + keepwin_data[1] - cnt_lose

    win_rate = cnt_win / (cnt_win + cnt_lose) * 100
    if win_rate < 95:
        url = 'https://i.imgur.com/adtGl7h.png'  # YOU LOSE
    else:
        url = 'https://i.imgur.com/1JXc9eD.png'  # YOU WIN

    return [cnt_win, cnt_lose, round(win_rate, 2), win_data, lose_data, keepwin_data, pts, url]


def ranking_output(type, guild):
    user = list(Zyanken_data.keys())
    users_data = []
    for i in range(len(user)):
        cnt_win = sum(Zyanken_data[user[i]]["win"].values())
        cnt_lose = sum(Zyanken_data[user[i]]["lose"].values())
        cnt_keepwin = Zyanken_data[user[i]]["keep"]["cnt"]
        cnt_maxwin = Zyanken_data[user[i]]["keep"]["max"]
        cnt = cnt_win + cnt_lose
        pts = cnt_keepwin * 3 + cnt_maxwin - cnt_lose
        users_data.append([int(user[i]), cnt_win, cnt_lose, (cnt_win / cnt) * 100, cnt_keepwin, cnt_maxwin, pts])

    stc = ""
    if type == "point":
        sort_data = sorted(users_data, key=itemgetter(6, 3), reverse=True)  # ポイント→勝率でソート
        i = 0
        while i < len(sort_data):
            if sort_data[i][1] + sort_data[i][2] < 100:  # 100戦以上
                sort_data.remove(sort_data[i])
                i -= 1
            i += 1

        j, k, flag, winner, loser = 1, 0, True, [], None
        for i in range(len(sort_data)):
            stc += f"{j}位 : {guild.get_member(sort_data[i][0]).display_name} " \
                   f"({sort_data[i][6]}点, 勝率{sort_data[i][3]:.02f}%, {sort_data[i][4]}連勝中)"
            if j <= 5:  # 5位以上の場合Winner
                stc += " [Winner]"
                winner.append(sort_data[i][0])
            elif j == 6:  # 6位の場合Loser
                stc += " [Loser]"
                loser = sort_data[i][0]
            stc += "\n"
            if i != len(sort_data) - 1:
                if sort_data[i][6] == sort_data[i + 1][6]:  # 同率の場合
                    k += 1
                else:
                    j, k = j + 1 + k, 0
            if j >= 6 and flag:  # 5位と6位の境目に区切り線を表示
                stc += f"{'-' * 50}\n"
                flag = False
        return "ポイント基準, 100戦以上", stc, winner, loser

    else:  # if type == "pointall":
        sort_data = sorted(users_data, key=itemgetter(6, 3), reverse=True)  # ポイント→勝率でソート

        for i in range(len(sort_data)):
            stc += f"{i + 1}位 : {guild.get_member(sort_data[i][0]).display_name} " \
                   f"({sort_data[i][6]}点, 勝率{sort_data[i][3]:.02f}%, {sort_data[i][4]}連勝中)"
            if i >= len(sort_data) - 2:  # ワースト2場合Loser
                stc += " [Loser]"
            stc += "\n"
        return "ポイント(>勝率>登録順)基準", stc, None, sort_data[len(sort_data) - 2][0]
