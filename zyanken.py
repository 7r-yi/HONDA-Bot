import random
import json


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


def honda_to_zyanken(my_hand, user):
    per_win = random.randint(1, 1000)
    if 774 <= per_win <= 780:  # 勝率0.7%
        win = True
    else:
        win = False

    if my_hand == "グー":
        my_hand = "r"
        if win:
            honda_hand = "チョキ"
            emoji1 = "✌"
        else:
            honda_hand = "パー"
            emoji1 = "✋"
    elif my_hand == "チョキ":
        my_hand = "s"
        if win:
            honda_hand = "パー"
            emoji1 = "✋"
        else:
            honda_hand = "グー"
            emoji1 = "✊"
    else:  # my_hand == "パー"
        my_hand = "p"
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
        data[str(user)]["win"][my_hand] += 1
    else:
        data[str(user)]["lose"][my_hand] += 1
    with open('zyanken_record.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))

    return img_pass, honda_hand, honda_word(win), emoji1, emoji2


def result_output(id):
    with open('zyanken_record.json', 'r') as f:
        data = json.load(f)

    cnt_win, cnt_lose = 0, 0
    win_data = list(data[str(id)]["win"].values())
    lose_data = list(data[str(id)]["lose"].values())
    for i in range(3):
        cnt_win += win_data[i]
    for i in range(3):
        cnt_lose += lose_data[i]

    return f"```★勝率{round((cnt_win / (cnt_win + cnt_lose)) * 100, 2)}% (計{cnt_win + cnt_lose}回)\n\n" \
           f"・YOU WIN {cnt_win}回\n" \
           f"(グー勝ち {win_data[0]}回, チョキ勝ち {win_data[1]}回, パー勝ち {win_data[2]}回)\n\n" \
           f"・YOU LOSE {cnt_lose}回\n" \
           f"(グー負け {lose_data[0]}回, チョキ負け {lose_data[1]}回, パー負け {lose_data[2]}回)```"
