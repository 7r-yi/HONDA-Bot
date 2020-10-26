import random
from operator import itemgetter
import constant


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
    if random.randint(1, 1000) % 142 != 0:  # 勝率99.3%
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

    data = constant.zyanken_data
    if str(user) not in constant.rm_user_data:  # 過去に退出したことがあるユーザーは記録しない
        if str(user) not in data:
            data[str(user)] = {"win": {"r": 0, "s": 0, "p": 0}, "lose": {"r": 0, "s": 0, "p": 0},
                               "keep": {"cnt": 0, "max": 0}}
        if win:
            data[str(user)]["win"][hiragana_to_alpha(my_hand)] += 1
            data[str(user)]["keep"]["cnt"] += 1
            if data[str(user)]["keep"]["cnt"] > data[str(user)]["keep"]["max"]:
                data[str(user)]["keep"]["max"] = data[str(user)]["keep"]["cnt"]
            data[str(constant.Honda)]["lose"][hiragana_to_alpha(honda_hand)] += 1
            data[str(constant.Honda)]["keep"]["cnt"] = 0
        else:
            data[str(user)]["lose"][hiragana_to_alpha(my_hand)] += 1
            data[str(user)]["keep"]["cnt"] = 0
            data[str(constant.Honda)]["win"][hiragana_to_alpha(honda_hand)] += 1
            data[str(constant.Honda)]["keep"]["cnt"] += 1
            if data[str(constant.Honda)]["keep"]["cnt"] > data[str(constant.Honda)]["keep"]["max"]:
                data[str(constant.Honda)]["keep"]["max"] = data[str(constant.Honda)]["keep"]["cnt"]
    constant.zyanken_data = data

    return img_pass, honda_hand, honda_word(win), emoji1, emoji2


def stats_output(id):
    cnt_win, cnt_lose = 0, 0
    win_data = list(constant.zyanken_data[str(id)]["win"].values())
    lose_data = list(constant.zyanken_data[str(id)]["lose"].values())
    keepwin_data = list(constant.zyanken_data[str(id)]["keep"].values())
    for i in range(3):
        cnt_win += win_data[i]
    for i in range(3):
        cnt_lose += lose_data[i]

    win_rate = cnt_win / (cnt_win + cnt_lose) * 100
    if win_rate < 99.3:
        url = 'https://i.imgur.com/adtGl7h.png'  # YOU LOSE
    else:
        url = 'https://i.imgur.com/1JXc9eD.png'  # YOU WIN

    return [cnt_win, cnt_lose, round(win_rate, 2), win_data, lose_data, keepwin_data, url]


def ranking_output(type, guild):
    user = list(constant.zyanken_data.keys())
    users_data = []
    for i in range(len(user)):
        cnt_win = sum(constant.zyanken_data[user[i]]["win"].values())
        cnt_lose = sum(constant.zyanken_data[user[i]]["lose"].values())
        cnt_keepwin = constant.zyanken_data[user[i]]["keep"]["cnt"]
        cnt_maxwin = constant.zyanken_data[user[i]]["keep"]["max"]
        cnt = cnt_win + cnt_lose
        users_data.append([int(user[i]), cnt_win, cnt_lose, (cnt_win / cnt) * 100, cnt_keepwin, cnt_maxwin])

    if type == "wins":
        sort_data = sorted(users_data, key=itemgetter(1, 3), reverse=True)  # 勝利数→勝率でソート
        i = 0
        while i < len(sort_data):
            if sort_data[i][3] < 100:  # 勝率100%未満は除外
                sort_data.remove(sort_data[i])
                i -= 1
            i += 1
        title = "勝利数(>登録順)基準, 無敗維持中"
    elif type == "winsall":
        sort_data = sorted(users_data, key=itemgetter(1, 3), reverse=True)  # 勝利数→勝率でソート
        title = "勝利数(>登録順)基準"
    elif type == "losesall":
        for i in range(len(users_data)):
            users_data[i][1] *= -1
        sort_data = sorted(users_data, key=itemgetter(2, 1), reverse=True)  # 敗北数→勝利数でソート
        for i in range(len(sort_data)):
            sort_data[i][1] *= -1
        title = "敗北数(>勝利数>登録順)基準"
    else:  # type == "winskeep"
        sort_data = sorted(users_data, key=itemgetter(4, 5), reverse=True)  # 連勝数→最大連勝数でソート
        title = "現在の連勝数基準"

    stc = ""
    if type == "wins":
        for i in range(len(sort_data)):
            stc += f"{i + 1}位 : {guild.get_member(sort_data[i][0]).display_name} " \
                   f"({sort_data[i][1]}勝{sort_data[i][2]}敗, 勝率{round(sort_data[i][3], 2):.02f}%)"
            stc += f" [Winner]\n{'-' * 50}\n" if i == 0 else "\n"
        return title, stc, sort_data[0][0], sort_data[len(sort_data) - 1][0]

    elif type == "winsall":
        for i in range(len(sort_data)):
            stc += f"{i + 1}位 : {guild.get_member(sort_data[i][0]).display_name} " \
                   f"({sort_data[i][1]}勝{sort_data[i][2]}敗, 勝率{round(sort_data[i][3], 2):.02f}%)"
            stc += " [Loser]\n" if i == len(sort_data) - 1 else "\n"
        return title, stc, sort_data[0][0], sort_data[len(sort_data) - 1][0]

    elif type == "losesall":
        for i in range(len(sort_data)):
            stc += f"{i + 1}位 : {guild.get_member(sort_data[i][0]).display_name} " \
                   f"({sort_data[i][2]}敗{sort_data[i][1]}勝, 勝率{round(sort_data[i][3], 2):.02f}%)"
            stc += " [Loser]\n" if i <= 1 else "\n"
        return title, stc, sort_data[1][0], None

    else:  # type == "winskeep"
        j, k, flag = 1, 0, True
        for i in range(len(sort_data)):
            stc += f"{j}位 : {guild.get_member(sort_data[i][0]).display_name} " \
                   f"(現在{sort_data[i][4]}連勝中, 最大{sort_data[i][5]}連勝)"
            stc += f" [Winner]\n" if j == 1 else "\n"
            if i != len(sort_data) - 1:
                if sort_data[i][4] == sort_data[i + 1][4]:
                    k += 1
                else:
                    j, k = j + 1 + k, 0
            if j > 1 and flag:
                stc += f"{'-' * 50}\n"
                flag = False
        return title, stc, sort_data[0][0], None
