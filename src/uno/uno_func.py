import random
import copy
import re

UNO_start = False

Rule = "★ハウスルール(基本的なものは除く)\n" \
       "1. 同じ数字/記号なら1ターンに何枚でも出せる (例 : 青1 → 青0, 緑0, 黄0)\n" \
       "1-2. 最初に出すカードは、直前の場札に対して出せるカードでないといけない\n" \
       "1-3. 最後に出すカードが、次の場札となる\n" \
       "2. スキップは、[2 × 出した枚数 - 1]人飛ばす\n" \
       "3. リバースは、奇数枚出すと進行順番が逆になる\n" \
       "3-2. 再度自分の番にはならない\n" \
       "4. ドロー4は、他に出せるカードがあっても出せる\n" \
       "4-2. ドロー2の後にドロー4で返すことが可能\n" \
       "4-3. ドロー4の後は、ドロー4もしくは指定された色のドロー2のみ返すことが可能\n" \
       "4-4. 一度にドロー2とドロー4を組み合わせて出すことも可能\n" \
       "5. ワイルドカードを出すと、色選択に加えてランダムに席順が入れ替わる\n" \
       "6. '7'を出すと、次の人の制限時間を[1 / (4 ^ 出した枚数)]に減らせる\n" \
       "6-2. 制限時間は[ターン開始時の手札の枚数 × 5 + 5]秒で、最小30秒～最大60秒\n" \
       "6-3. '7'の妨害効果は最小30秒の制限を無視する\n" \
       "7. 山札から引いた後にすぐ出すことができる、そこから手札と組見合わせて出すことも可能\n" \
       "7-2. ドロー2/4を受けた後でもカードを出すことが可能\n" \
       "8. ディスカードオールは、出したカードと同じ色の手札を全て捨てる\n" \
       "8-2. ディスカードオールで上がることは出来ない(カードを捨てた後に2枚追加)\n" \
       "9. ドボンカードは、自分以外の全員にカードを引かせる\n" \
       "9-2. 相手に出されたら、ドボンカードのみで返すことが可能\n" \
       "9-3. 最後にドボンカードを出した人以外の全員が引く\n" \
       "10. 山札から引けるのは1ターンで1枚まで\n" \
       "10-2. 山札から1枚も引かずにパスすることは出来ない(ドローやドボンを受ける場合は除く)\n" \
       "11. 記号で上がることは出来ない(記号しか残っていない時点で2枚追加)\n" \
       "12. 誰か1人が上がったらその時点でゲームセット\n" \
       "12-2. 数字カードは-その数字点、記号カードは-20点、ディスカードオールは-30点、ワイルドカードは-50点\n" \
       "12-3. 1位は全員のマイナスポイント分をプラスで受け取れる\n\n\n" \
       "★カードの出し方 ※[]内は短縮形\n" \
       "・数字カード → 赤0 [R0], 青1 [B1], 緑2 [G2], 黄3 [Y3]\n" \
       "・記号カード → 赤スキップ [RS], 青リバース [BR], 緑ドロー2 [G+2, GD2], 黄ディスカードオール [YDA]\n" \
       "・ワイルドカード → ワイルド [W], ドロー4 [+4, D4], ドボン1 [+1, D1], ドボン2 [+2, D2]\n\n" \
       "1. 複数枚出す時はカンマで区切る (例 : 赤0, 青0, 赤0, 緑0)\n" \
       "1-2. カンマ以外にも空白、読点、コンマなどでも可能\n" \
       "2. ワイルドカードを出したらその後に色指定の時間があるので、そこで希望する色を入力する\n" \
       "3. 山札からカードを1枚引く場合は !Get [!G] と入力する\n" \
       "4. カードを出さない場合は !Pass [!P] と入力する\n" \
       "5. 残り1枚になった後は !UNO と入力する\n" \
       "5-2. 残り手札が複数枚でも、次の1ターンで上がれる手札だったら !UNO と入力する必要あり\n" \
       "5-3. UNOと宣言せずに上がる or 指摘されると2枚ペナルティー\n" \
       "5-4. 他プレイヤーにUNOを指摘する際は メンション !UNO と入力する (例 : @そばゆ !UNO)\n" \
       "5-5. UNOとなる人のターンが終了してから10秒間は指摘出来ない\n" \
       "5-6. 再度自分のターンになるまでに、指摘ミスを2回行うとペナルティー(次の自分のターンが1回強制パス)\n\n\n" \
       "★その他ゲーム中のコマンド\n" \
       "・ゲームに途中参加する → !Join\n" \
       "・ゲームから離脱する → !Drop (ペナルティーとして、離脱時点での手札の点-100点 減点)\n" \
       "・ゲームから離脱させる → メンション !Drop (モデレーターのみ)\n" \
       "・ゲームを中止する → !Cancel (過半数の同意が必要)"

Card_Template = "```・数字の0 : 各色[1]枚ずつ\n・数字の7 : 各色[2]枚ずつ\n・数字の1～6, 8～9 : 各色[2]枚ずつ\n" \
                "・スキップ : 各色[2]枚ずつ\n・リバース : 各色[2]枚ずつ\n" \
                "・ドロー2 : 各色[2]枚ずつ\n・ディスカードオール : 各色[1]枚ずつ\n" \
                "・ワイルド : 全部で[4]枚\n・ドロー4 : 全部で[4]枚\n・ドボン1 : 全部で[2]枚\n・ドボン2 : 全部で[1]枚```"

# 0とディスカードオールは各色1枚ずつ、他は各色2枚ずつ、ワイルドカードは4枚ずつ
Card = []
Color = ["赤", "青", "緑", "黄"]
Number = [str(i) for i in range(10)] + ["スキップ", "リバース", "ドロー2", "ディスカードオール"]
for n1 in Number:
    for n2 in Color:
        Card.append(f"{n2}{n1}")
Card = (Card * 2)[4:-4] + ["ワイルド", "ドロー4"] * 4 + ["ドボン1"] * 2 + ["ドボン2"]
Card_Normal = Card


def template_check(stc):
    stc = stc.replace("]", "[")
    if stc.count("[") != 22:
        return "データ数が間違っていたり、[]で囲まれていない箇所があるかもしれません"

    data = stc.split("[")
    card_num = []
    for i in range(11):
        if not data[i * 2 + 1].isdecimal():
            return "[]内が数字のみとなっていない箇所があります"
        elif not 0 <= int(data[i * 2 + 1]) <= 100:
            return "枚数設定の可能な範囲は、それぞれ0～100枚です"
        card_num.append(int(data[i * 2 + 1]))
    if all([card_num[i] == 0 for i in range(3)]):
        return "数字カードを全て0枚に設定することは出来ません"

    # カードの枚数設定に応じて新カードを生成
    mark = ["0", "7", "9", "スキップ", "リバース", "ドロー2", "ディスカードオール", "ワイルド", "ドロー4", "ドボン1", "ドボン2"]
    marks, new_card = [], []
    for i in range(7):
        for j in range(card_num[i]):
            marks.append(mark[i])
    for i in range(card_num[2]):
        marks += [str(j) for j in range(1, 7)] + ["8"]
    for n in marks:
        for m in Color:
            new_card.append(f"{m}{n}")
    for i in range(-1, -5, -1):
        for j in range(card_num[i]):
            new_card.append(mark[i])
    global Card
    Card = new_card

    return None


def translate_input(word):
    if word in ["w", "wild", "ヒカキン", "hikakin"]:
        return "ワイルド"
    elif word in ["+4", "d4", "draw4", "ケイスケホンダ"]:
        return "ドロー4"
    elif word in ["+1", "d1", "dobon1", "英孝1", "狩野英孝1", "eikogo!1"]:
        return "ドボン1"
    elif word in ["+2", "d2", "dobon2", "英孝2", "狩野英孝2", "eikogo!2"]:
        return "ドボン2"
    else:
        trans1, trans2 = word[0], word[1:]
        if trans1 == "r":
            trans1 = "赤"
        elif trans1 == "b":
            trans1 = "青"
        elif trans1 == "g":
            trans1 = "緑"
        elif trans1 == "y":
            trans1 = "黄"
        if trans2 in ["s", "skip"]:
            trans2 = "スキップ"
        elif trans2 in ["r", "reverse"]:
            trans2 = "リバース"
        elif trans2 in ["+2", "d2", "draw2", "ダブルピース"]:
            trans2 = "ドロー2"
        elif trans2 in ["da", "discardall", "修造", "松岡修造"]:
            trans2 = "ディスカードオール"
        return f"{trans1}{trans2}"


def card_to_string(card):
    if not card:
        return "なし"
    else:
        return ', '.join(card)


def string_to_card(stc):
    stc = re.sub('[.、\s]', ',', stc).replace("色", "")
    if stc.count(",") >= 1:  # 出すカードをリスト化
        card, cards = stc.split(","), []
        for i in range(len(card)):
            if card[i].strip() != "":
                cards.append(translate_input(card[i].strip()))
        if not cards:
            return [stc]
        else:
            return cards
    else:
        return [translate_input(stc.strip())]


# 赤100番台, 青200番台,　緑300番台, 黄400番台, ワイルド530～534, ドロー4 540～544, ドボン1 550～554, ドボン2 560～564
def card_to_id(card):
    if "ワイルド" in card:
        for i in range(len(Color)):
            if card[0] == Color[i]:
                return 530 + (i + 1)
        return 530
    elif "ドロー4" in card:
        for i in range(len(Color)):
            if card[0] == Color[i]:
                return 540 + (i + 1)
        return 540
    elif "ドボン1" in card:
        for i in range(len(Color)):
            if card[0] == Color[i]:
                return 550 + (i + 1)
        return 550
    elif "ドボン2" in card:
        for i in range(len(Color)):
            if card[0] == Color[i]:
                return 560 + (i + 1)
        return 560
    else:
        for i in range(len(Color)):
            if card[0] == Color[i]:
                for j in range(len(Number)):
                    if card[1:] == Number[j]:
                        return (i + 1) * 100 + j


def id_to_card(id):
    if id < 500:
        return f"{Color[id // 100 - 1]}{Number[id % 100]}"
    elif 530 <= id <= 534:
        return "ワイルド"
    elif 540 <= id <= 544:
        return "ドロー4"
    elif 550 <= id <= 554:
        return "ドボン1"
    else:
        return "ドボン2"


def number_card():
    while True:
        card = random.choice(Card)
        if card_to_id(card) % 100 <= 9:
            return card


def deal_card(num):
    hand = []
    for _ in range(num):
        hand.append(random.choice(Card))

    return hand


# 数字/記号が揃うように並べ替える
def sort_card(cards):
    card_id = []
    for card in cards:
        id = card_to_id(card)
        card_id.append([id % 100, id])
    card_id.sort()
    cards = []
    for id in card_id:
        cards.append(id_to_card(id[1]))

    return cards


def check_card(before, after, hand, penalty):
    before, first = card_to_id(before), card_to_id(after[0])
    hand_tmp, card = copy.copy(hand), ""

    # 出すカードを手札から全て削除 → エラーを吐いたら持ってないカードあり
    try:
        for card in after:
            hand_tmp.remove(card)
    except ValueError:
        if card in hand:
            return f"{card} を出す枚数が、手札に対して多すぎます"
        elif card in Card:
            return f"{card} は持っていません"
        else:
            return f"{card} ってカードは存在しませんよ(笑)"

    # NG上がり判定
    # if hand_tmp == [] and len(hand) >= 2:
    # return "複数枚出しで上がることは出来ません"
    if hand_tmp == [] and first % 100 > 9:
        return "記号で上がることは出来ません"

    # 出したカードの全ての記号が一致するか判定
    if all([first % 100 == card_to_id(i) % 100 for i in after]):
        pass
    elif "ドロー" in after[0]:
        # ドロー2/4以外が含まれているか判定
        if not all(["ドロー" in i for i in after]):
            return "ドロー2/4と一緒に出せるのは、ドロー2/4のみです"
    elif "ドボン" in after[0]:
        # ドボン1/2以外が含まれているか判定
        if not all(["ドボン" in i for i in after]):
            return "ドボン1/2と一緒に出せるのは、ドボン1/2のみです"
    else:
        return "出したカードの中に、他のカードと数字/記号が異なっているカードがあります"

    # 場のカードが効果継続中のドロー2の場合
    if before % 100 == 12 and penalty > 0:
        if first % 100 != 12 and first != 540:
            return "ドロー2には、ドロー2/4でしか返せません"
    # 場のカードが効果継続中のドロー4の場合
    elif 540 <= before <= 544 and penalty > 0:
        if not (before % 540 == first // 100 and first % 100 == 12) and first != 540:
            return "ドロー4には、色が合っているドロー2またはドロー4でしか返せません"
    # 場のカードが効果継続中のドボン1/2の場合
    elif 550 <= before <= 564 and penalty > 0:
        if first != 550 and first != 560:
            return "ドボン1/2には、ドボン1/2でしか返せません"

    # 場札と最初のカードの色が一致
    if before // 100 == first // 100:
        pass
    # ワイルドカードの色判定
    elif before > 500 and before % 10 == first // 100:
        pass
    # 色を無視してワイルドカードを出す
    elif first > 500:
        pass
    # 色は異なるが記号が一致
    elif before % 100 == first % 100:
        pass
    else:
        return "場札のカードと、最初に出すカードの色が一致していません"

    return None


def check_win(cards):
    check_id = card_to_id(cards[0]) % 100
    if check_id > 9:
        return False

    for card in cards:
        if card_to_id(card) % 100 != check_id:
            return False

    return True


def search_player(player, all_data):
    for j in range(len(all_data)):
        if all_data[j][0] == player:
            return j

    return None


def calculate_penalty(cards):
    penalty = 0
    for card in cards:
        if "ドロー2" in card:
            penalty += 2
        elif card == "ドロー4":
            penalty += 4
        elif card == "ドボン1":
            penalty += 1
        elif card == "ドボン2":
            penalty += 2

    return penalty


def remove_color_card(color, hand):
    color_id = Color.index(color) + 1
    hand_tmp = copy.copy(hand)
    for card in hand:
        if card_to_id(card) // 100 == color_id:
            hand_tmp.remove(card)

    return hand_tmp
