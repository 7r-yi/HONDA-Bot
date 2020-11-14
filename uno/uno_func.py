import random
import copy

UNO_start = False
Rule = "★ハウスルール(基本的なものは除く)\n" \
       "1. 同じ数字/記号なら1ターンで何枚でも出せる (例 : 赤0 → 青0, 緑0, 黄0)\n" \
       "1-2. 最後に出すカードの色が、次の場のカードの色となる\n" \
       "2. スキップは[2 × 出した枚数 - 1]人飛ばす\n" \
       "3. リバースを出しても再度自分の番にはならない\n" \
       "4. ドロー4は他に出せるカードがあっても出せる\n" \
       "4-2. ドロー2の後にドロー4で返すことが可能\n" \
       "4-3. ドロー4の後は、ドロー4もしくは指定された色のドロー2のみ返すことが可能\n" \
       "4-4. 一度にドロー2とドロー4を組み合わせて出すことは出来る\n" \
       "5. ワイルドカードを出すと、色選択に加えてランダムに席順が入れ替わる\n" \
       "6. 山札から引いた後にすぐ出すことができる、そこから手札とコンボを組んでも良い\n" \
       "6-2. ドロー2/4を受けた後でもカードを出すことが出来る\n" \
       "7. 山札から引けるのは1ターンで1枚まで\n" \
       "7-2. 山札から1枚も引かずにパスすることは出来ない(ドロー2/4を受ける場合は除く)\n" \
       "8. 記号で上がることは出来ない(記号しか残っていない時点で2枚追加)\n" \
       "8-2. 手札が2枚以上の状態から、複数枚出しで一気に上がることは出来ない\n" \
       "9. 誰か1人が上がったらその時点でゲームセット\n" \
       "9-2. 数字カードは-その数字点、記号カードは-20点、ワイルドカードは-50点で計算\n" \
       "9-3. 1位は全員のマイナスポイント分をプラスで受け取れる\n\n\n" \
       "★カードの出し方 ※[]内は短縮形\n" \
       "・数字カード → 赤0 [R0], 青1 [B1], 緑2 [G2], 黄3 [Y3] など\n" \
       "・記号カード → 赤スキップ [RS], 青リバース [BR], 緑ドロー2 [G+2, GD2] など\n" \
       "・ワイルドカード → ワイルド [W], ドロー4 [+4, D4]\n\n" \
       "1. 複数枚出し時はカンマで区切る (例 : 赤0, 青0, 赤0, 緑0)\n" \
       "2. ワイルドカードを出す時は ワイルド or ドロー4 と入力する\n" \
       "2-2. その後色指定の時間があるので、赤 or 青 or 緑 or 黄 と入力する\n" \
       "3. 山札からカードを1枚引く場合は !Get [!G] と入力する\n" \
       "4. カードを出さない場合は !Pass [!P] と入力する\n" \
       "5. 残り1枚になった後は !UNO と入力する\n" \
       "5-2. 他プレイヤーのUNO宣言忘れを指摘する際は メンション !UNO と入力する (例 : @そばゆ !UNO)\n" \
       "5-3. 残り1枚となる人のターンが終了してから10秒間は指摘出来ない\n" \
       "5-4. UNOと宣言せずに上がる or 指摘されると2枚ペナルティー\n\n\n" \
       "★その他コマンド\n" \
       "・ゲームに途中参加する → !Join\n" \
       "・ゲームから離脱する → !Drop (確定負け & 手札の点-100点)\n" \
       "・ゲームから離脱させる → メンション !Drop (モデレーターのみ)\n" \
       "・ゲームを中止する → !Cancel (過半数の同意が必要)"

Card = []
Color = ["赤", "青", "緑", "黄"]
Number = [str(i) for i in range(10)] + ["スキップ", "リバース", "ドロー2"]
for n1 in Color:
    for n2 in Number:
        Card.append(f"{n1}{n2}")
Card = (Card * 2)[4:] + ["ワイルド", "ドロー4"] * 4  # 0は各色1枚ずつ、他は各色2枚ずつ、ワイルドカードは4枚ずつ


def translate_input(word):
    word = word.replace("色", "")
    if word == "w":
        return "ワイルド"
    elif word in ["+4", "d4"]:
        return "ドロー4"
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
        if trans2 == "s":
            trans2 = "スキップ"
        elif trans2 == "r":
            trans2 = "リバース"
        elif trans2 in ["+2", "d2"]:
            trans2 = "ドロー2"
        return f"{trans1}{trans2}"


def card_to_string(card):
    if not card:
        return "なし"
    else:
        return ', '.join(card)


def string_to_card(stc):
    if stc.count(",") >= 1:  # 出すカードをリスト化
        stc, card = stc.split(","), []
        for i in range(len(stc)):
            if stc[i].strip() != "":
                card.append(translate_input(stc[i].strip()))
        return card

    else:
        return [translate_input(stc.strip())]


def card_to_id(card):
    for i in range(len(Color)):
        if card[0] == Color[i]:
            for j in range(len(Number)):
                if card[1:] == Number[j]:
                    return (i + 1) * 100 + j
    if "ワイルド" in card:
        return 510
    else:  # ドロー4
        return 511


def id_to_card(id):
    if id < 500:
        return f"{Color[id // 100 - 1]}{Number[id % 100]}"
    elif id == 510:
        return "ワイルド"
    else:  # id == 511
        return "ドロー4"


def first_card():
    return [Card[random.randint(0, len(Card) - 9)]]


def deal_card(num):
    hand = []
    for _ in range(num):
        hand.append(Card[random.randint(0, len(Card) - 1)])

    return hand


def sort_card(card):
    card_id = []
    for i in card:
        card_id.append(card_to_id(i))
    card_id.sort()
    card = []
    for i in card_id:
        card.append(id_to_card(i))

    return card


def check_card(before, after, hand, penalty):
    error = None
    hand_tmp, card = copy.copy(hand), ""

    # 場のカードがドロー2の場合
    if "ドロー2" in before and penalty > 0:
        if not all(["ドロー" in i for i in after]):
            error = "ドロー2にはドロー2/4でしか返せません"
    # 場のカードがドロー4の場合
    elif "ドロー4" in before and penalty > 0:
        if not ((before[0] == after[0][0] and after[0][1:] == "ドロー2") or after[0] == "ドロー4"):
            error = "ドロー4には、色が合っているドロー2またはドロー4でしか返せません"
        elif not all(["ドロー" in i for i in after]):
            error = "その複数枚の出し方は出来ません(ドロー2/4と一緒に出せるのはドロー2/4のみ)"
    # 場のカードが効果の消えたドロー or 色カードの場合
    else:
        # ワイルドorドロー4じゃない場合
        if after[0] not in ["ワイルド", "ドロー4"]:
            # 先頭カードの色も数字も合ってない
            if before[0] != after[0][0] and before[1:] != after[0][1:]:
                error = "そのカードは出せません(場札のカードと色または数字/記号が一致していない)"
            elif not all([after[0][1:] == after[i][1:] for i in range(len(after))]):
                error = "その複数枚の出し方は出来ません(数字/記号が異なっているカードがある)"
        # ワイルドカードの場合
        elif after[0] == "ワイルド":
            if not all([i == "ワイルド" for i in after]):
                error = "その複数枚の出し方は出来ません(ワイルドカードは他の種類のカードと組み合わせられない)"
        # ドロー4の場合
        else:
            if not all(["ドロー" in i for i in after]):
                error = "その複数枚の出し方は出来ません(ドロー2/4と一緒に出せるのはドロー2/4のみ)"

    if after == hand and len(hand) >= 2:
        error = "複数枚出しで一気に上がることが出来ません"
    # 出すカードを手札から全て削除 → エラーを吐いたら持ってないカードあり
    try:
        for card in after:
            hand_tmp.remove(card)
    except ValueError:
        error = f"{card} ってカードは存在しない/持っていません"

    return error is None, error


def search_player(player, all_data):
    for j in range(len(all_data)):
        if all_data[j][0] == player:
            return j
    return None


def calculate_penalty(card):
    penalty = 0
    for i in card:
        if "ドロー2" in i:
            penalty += 2
        elif i == "ドロー4":
            penalty += 4

    return penalty
