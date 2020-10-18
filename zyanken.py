import random
import json
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
    per_win = random.randint(1, 1000)
    if 774 <= per_win <= 780:  # 勝率0.7%
        win = True
    else:
        win = False

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

    if win:
        img_pass = './image/YOU WIN.jpg'
        emoji2 = "👏"
    else:
        img_pass = './image/YOU LOSE.jpg'
        emoji2 = "👎"

    with open('zyanken_record.json', 'r') as f:
        data = json.load(f)
    if str(user) not in data:
        data[str(user)] = {"win": {"r": 0, "s": 0, "p": 0}, "lose": {"r": 0, "s": 0, "p": 0}}
    if win:
        data[str(user)]["win"][hiragana_to_alpha(my_hand)] += 1
        data[str(constant.Honda)]["lose"][hiragana_to_alpha(honda_hand)] += 1
    else:
        data[str(user)]["lose"][hiragana_to_alpha(my_hand)] += 1
        data[str(constant.Honda)]["win"][hiragana_to_alpha(honda_hand)] += 1
    with open('zyanken_record.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))

    return img_pass, honda_hand, honda_word(win), emoji1, emoji2


def stats_output(id):
    with open('zyanken_record.json', 'r') as f:
        data = json.load(f)

    cnt_win, cnt_lose = 0, 0
    win_data = list(data[str(id)]["win"].values())
    lose_data = list(data[str(id)]["lose"].values())
    for i in range(3):
        cnt_win += win_data[i]
    for i in range(3):
        cnt_lose += lose_data[i]

    win_rate = cnt_win / (cnt_win + cnt_lose) * 100
    if win_rate < 0.7:
        url = 'https://i.imgur.com/adtGl7h.png'  # YOU LOSE
    else:
        url = 'https://i.imgur.com/1JXc9eD.png'  # YOU WIN

    return [cnt_win, cnt_lose, round(win_rate, 2), win_data, lose_data, url]


def ranking_output(type):
    with open('zyanken_record.json', 'r') as f:
        data = json.load(f)

    user = list(data.keys())
    users_data, user_id, user_win, user_rate, user_lose = [], [], [], [], []
    for i in range(len(user)):
        cnt_win = sum(data[user[i]]["win"].values())
        cnt_lose = sum(data[user[i]]["lose"].values())
        cnt = cnt_win + cnt_lose
        users_data.append([int(user[i]), cnt_win, cnt_lose, cnt, (cnt_win / cnt) * 100])
        user_id.append(int(user[i]))
        user_win.append(cnt_win)
        user_lose.append(cnt_lose)
        user_rate.append((cnt_win / cnt) * 100)

    if type == "wins":
        sort_data = sorted(zip(tuple(user_win), tuple(user_id), tuple(user_rate), tuple(user_lose)), reverse=True)
    else:  # type == "rate"
        sort_data = sorted(zip(tuple(user_rate), tuple(user_id), tuple(user_win), tuple(user_lose)), reverse=True)
    sort_data = list(map(list, sort_data))

    for i in range(len(users_data)):
        for j in range(1, len(users_data) - i):
            if sort_data[i][0] == sort_data[i + j][0]:
                if sort_data[i][2] < sort_data[i + j][2]:  # 勝利数でソート
                    tmp = sort_data[i]
                    sort_data[i] = sort_data[i + j]
                    sort_data[i + j] = tmp
                elif sort_data[i][2] == sort_data[i + j][2]:  # 勝利数=0 → 敗北数でソート
                    if sort_data[i][3] > sort_data[i + j][3]:
                        tmp = sort_data[i]
                        sort_data[i] = sort_data[i + j]
                        sort_data[i + j] = tmp
            else:
                break

    return users_data, sort_data
