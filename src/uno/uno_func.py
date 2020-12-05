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
       "4-4. 一度にドロー2とドロー4を組み合わせて出すことは出来る\n" \
       "5. ワイルドカードを出すと、色選択に加えてランダムに席順が入れ替わる\n" \
       "6. '7'を出すと、次の人の制限時間を[1 / (3 ^ 出した枚数)]に減らせる\n" \
       "6-2. 制限時間は[ターン開始時の手札の枚数 × 5 + 5]秒で、最小30秒～最大60秒\n" \
       "6-3. '7'の妨害効果は最小30秒の制限を無視する\n" \
       "7. 山札から引いた後にすぐ出すことができる、そこから手札とコンボを組んでも良い\n" \
       "7-2. ドロー2/4を受けた後でもカードを出すことが出来る\n" \
       "8. ディスカードオールは、出したカードと同じ色の手札を全て捨てる\n" \
       "8-2. ディスカードオールで上がることは出来ない(カードを捨てた後に2枚追加)\n" \
       "9. 山札から引けるのは1ターンで1枚まで\n" \
       "9-2. 山札から1枚も引かずにパスすることは出来ない(ドロー2/4を受ける場合は除く)\n" \
       "10. 記号で上がることは出来ない(記号しか残っていない時点で2枚追加)\n" \
       "10-2. 手札が2枚以上の状態から、複数枚出しで一気に上がることは出来ない\n" \
       "11. 誰か1人が上がったらその時点でゲームセット\n" \
       "11-2. 数字カードは-その数字点、記号カードは-20点、ディスカードオールは-30点、ワイルドカードは-50点\n" \
       "11-3. 1位は全員のマイナスポイント分をプラスで受け取れる\n\n\n" \
       "★カードの出し方 ※[]内は短縮形\n" \
       "・数字カード → 赤0 [R0], 青1 [B1], 緑2 [G2], 黄3 [Y3] など\n" \
       "・記号カード → 赤スキップ [RS], 青リバース [BR], 緑ドロー2 [G+2, GD2], 黄ディスカードオール[黄ディス, YDA] など\n" \
       "・ワイルドカード → ワイルド [W], ドロー4 [+4, D4]\n\n" \
       "1. 複数枚出す時はカンマで区切る (例 : 赤0, 青0, 赤0, 緑0)\n" \
       "1-2. カンマ以外にも空白、読点、コンマなどでも可能\n" \
       "2. ワイルドカードを出す時は ワイルド or ドロー4 と入力する\n" \
       "2-2. その後に色指定の時間があるので、赤 or 青 or 緑 or 黄 or ランダム と入力する\n" \
       "3. 山札からカードを1枚引く場合は !Get [!G] と入力する\n" \
       "4. カードを出さない場合は !Pass [!P] と入力する\n" \
       "5. 残り1枚になった後は !UNO と入力する\n" \
       "5-2. 他プレイヤーのUNO宣言忘れを指摘する際は メンション !UNO と入力する (例 : @そばゆ !UNO)\n" \
       "5-3. 残り1枚となる人のターンが終了してから10秒間は指摘出来ない\n" \
       "5-4. UNOと宣言せずに上がる or 指摘されると2枚ペナルティー\n\n\n" \
       "★その他ゲーム中のコマンド\n" \
       "・ゲームに途中参加する → !Join\n" \
       "・ゲームから離脱する → !Drop (ペナルティーとして、離脱時点での手札の点-100点 減点)\n" \
       "・ゲームから離脱させる → メンション !Drop (モデレーターのみ)\n" \
       "・ゲームを中止する → !Cancel (過半数の同意が必要)"

# 0とディスカードオールは各色1枚ずつ、他は各色2枚ずつ、ワイルドカードは4枚ずつ
Card = []
Color = ["赤", "青", "緑", "黄"]
Number = [str(i) for i in range(10)] + ["スキップ", "リバース", "ドロー2", "ディスカードオール"]
for n1 in Number:
    for n2 in Color:
        Card.append(f"{n2}{n1}")
Card = (Card * 2)[4:-4] + ["ワイルド", "ドロー4"] * 4


def translate_input(word):
    if word in ["w", "wild", "ドリラー"]:
        return "ワイルド"
    elif word in ["+4", "d4", "draw4", "ケイスケホンダ"]:
        return "ドロー4"
    else:
        trans1, trans2 = word[0], word[1:]
        if trans1 in ["r", "red"]:
            trans1 = "赤"
        elif trans1 in ["b", "blue"]:
            trans1 = "青"
        elif trans1 in ["g", "green"]:
            trans1 = "緑"
        elif trans1 in ["y", "yellow"]:
            trans1 = "黄"
        if trans2 in ["s", "skip"]:
            trans2 = "スキップ"
        elif trans2 in ["r", "reverse"]:
            trans2 = "リバース"
        elif trans2 in ["+2", "d2", "draw2", "ダブルピース"]:
            trans2 = "ドロー2"
        elif trans2 in ["da", "discardall", "ディス", "修造"]:
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


# 赤100番台, 青200番台,　緑300番台, 黄400番台, ワイルド530～534, ドロー4 540～544
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
    else:  # 540 <= id <= 544
        return "ドロー4"


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

    # カード全出し
    if hand_tmp == [] and len(hand) >= 2:
        return "複数枚出しで上がることは出来ません"

    # 出したカードの全ての記号が一致するか判定
    if all([first % 100 == card_to_id(i) % 100 for i in after]):
        pass
    elif "ドロー" in after[0]:
        # ドロー2/4以外が含まれているか判定
        if not all(["ドロー" in i for i in after]):
            return "ドロー2/4と一緒に出せるのは、ドロー2/4のみです"
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

    return penalty


def remove_color_card(color, hand):
    color_id = Color.index(color) + 1
    hand_tmp = copy.copy(hand)
    for card in hand:
        if card_to_id(card) // 100 == color_id:
            hand_tmp.remove(card)

    return hand_tmp
