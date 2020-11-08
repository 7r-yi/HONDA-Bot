import random
import json

UNO_start = False
Rule = "★ハウスルール(基本的なものは除く)\n" \
       "1. 同じ数字/記号なら1ターンで何枚でも出せる (例 : 赤0 → 青0 + 緑0 + 黄0)\n" \
       "1-2. 最後に出すカードの色が、次の場のカードの色となる\n" \
       "2. リバースを出しても再度自分の番にはならない\n" \
       "3. ドロー4は他に出せるカードがあって手も出せる\n" \
       "3-2. ドロー2の後にドロー4で返すことが可能\n" \
       "3-3. ドロー4の後は、ドロー4もしくは指定された色のドロー2のみ返すことが可能\n" \
       "3-4. 一度にドロー2とドロー4を組み合わせて出すことは出来る\n" \
       "4. 山札から引いた後でもすぐ出すことができ、手持ちと組み合わせても良い\n" \
       "4-2. ドロー2/4を受けた後でもカードを出すことが出来る\n" \
       "5. 記号で上がることは出来ない (記号しか残っていない時点で2枚追加)\n" \
       "5-2. 手札が2枚以上の状態から、複数枚出しで一気に上がることは出来ない\n" \
       "6. 誰か1人が上がったらその時点でゲームセット\n" \
       "6-2. 数字カードは-その数字点、記号カードは-20点、ワイルドカードは-50点で計算\n" \
       "6-3. 1位は全員のマイナスポイント分をプラスで受け取れる\n\n" \
       "★カードの出し方\n" \
       "・数字カード → 赤0 or 青1 or 緑2 or 黄3 など\n" \
       "・記号カード → 赤スキップ or 青リバース or 緑ドロー2 など\n" \
       "・ワイルドカード → ワイルド or ドロー4\n" \
       "1. 複数枚出し時はカンマで区切る (例 : 赤0, 青0, 赤0, 緑0)\n" \
       "2. ワイルドカードを出す時は ワイルド or ドロー4 と入力する\n" \
       "2-2. その後色指定の時間があるので、赤　or　青　or　緑　or　黄 と入力する\n" \
       "3. 山札からカードを1枚引く場合は !Get と入力する" \
       "4. カードを出さない場合は !Pass と入力する\n" \
       "5. 残り1枚になった後は !UNO と入力する\n" \
       "5-2. 他プレイヤーのUNO宣言忘れを指摘する際は メンション !UNO と入力する (例 : @そばゆ !UNO)\n" \
       "5-3. 残り1枚となる人のターンが終了してから5秒間は指摘出来ない"

Card = []
Color = ["赤", "青", "緑", "黄"]
Number = [str(i) for i in range(10)] + ["スキップ", "リバース", "ドロー2"]
for n1 in Color:
    for n2 in Number:
        Card.append(f"{n1}{n2}")
Card = (Card * 2)[4:] + ["ワイルド", "ドロー4"] * 4  # 0は各色1枚ずつ、他は各色2枚ずつ、ワイルドカードは4枚ずつ

with open('uno/uno_record.json', 'r') as f:
    Player_data = json.load(f)


def card_to_string(card):
    stc = ""
    for i in card:
        stc += f"{i}, "

    return stc[:-2]


def string_to_card(stc):
    if stc.count(",") >= 1:  # 出すカードをリスト化
        stc = stc.split(",")
        return [stc[i].strip() for i in range(len(stc))]
    else:
        return [stc.strip()]


def card_to_id(card):
    for i in range(len(Color)):
        if card[0] == Color[i]:
            for j in range(len(Number)):
                if card[1:] == Number[j]:
                    return (i + 1) * 100 + j
    if card == "ワイルド":
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


def deal_card(num):
    hand, stc = [], ""
    for _ in range(num):
        hand.append(Card[random.randint(0, len(Card))])

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


def check_card(before, after, hand):
    error = None
    if "ドロー2" in before:  # 場のカードがドロー2の場合
        if not all(["ドロー" in i for i in after]):  # ドロー2/4以外のカードがある
            error = "ドロー2にはドロー2/4でしか返せません"
    elif "ドロー4" in before:  # 場のカードがドロー4の場合
        if not ((before[0] == after[0][0] and after[0][1:] == "ドロー2") or after[0] == "ドロー4"):  # 返さないカードとなっている
            error = "ドロー4には、色が合っているドロー2またはドロー4でしか返せません"
        elif not all(["ドロー" in i for i in after]):  # ドロー2/4以外のカードがある
            error = "その複数枚の出し方は出来ません(ドロー2/4しか出せない)"
    else:  # 場のカードが4色の場合
        if after[0] not in ["ワイルド", "ドロー4"]:  # ワイルドorドロー4じゃない場合
            if before[0] != after[0][0] and before[1:] != after[0][1:]:  # 先頭カードの色も数字も合ってない
                error = "そのカードは出せません"
            elif not all([after[0][1:] == after[i][1:] for i in range(len(after))]):  # 複数枚出しの時、数字が異なっている
                error = "その複数枚の出し方は出来ません(数字/記号が異なっているカードがある)"
        elif after[0] == "ワイルド":  # ワイルドカードの場合
            if all([i == "ワイルド" for i in after]):  # ワイルドカードでないものがある
                error = "その複数枚の出し方は出来ません(ワイルドカードしか出せない)"
        else:  # ドロー4の場合
            if not all(["ドロー" in i for i in after]):  # ドロー2/4以外のカードがある
                error = "その複数枚の出し方は出来ません(ドロー2/4しか出せない)"
    for i in after:
        if i not in hand:
            error = "持っていないカードが含まれています"
    if after == hand and len(hand) >= 2:
        error = "複数枚出しで一気に上がることが出来ません"

    if error is None:
        return True, ""
    else:
        return False, ""


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


def calculate_point(card):
    pts = 0
    for i in card:
        id = card_to_id(i)
        if id % 100 <= 9 and id < 500:  # 数字カードはその数字の点数
            pts -= id % 100
        elif id < 500:  # 記号カードは20点
            pts -= 20
        else:  # ワイルドカードは50点
            pts -= 50

    return pts


def data_output(data):
    for i in range(len(data)):
        if str(data[i][0]) not in Player_data:
            Player_data[str(data[i][0])] = {"win": 0, "lose": 0, "point": 0, "max": 0, "min": 0}
        if data[i][4] > 0:
            Player_data[str(data[i][0])]["win"] += 1
        else:
            Player_data[str(data[i][0])]["lose"] += 1
        Player_data[str(data[i][0])]["point"] += data[i][4]
        if Player_data[str(data[i][0])]["max"] < data[i][4]:
            Player_data[str(data[i][0])]["max"] = data[i][4]
        elif Player_data[str(data[i][0])]["min"] > data[i][4]:
            Player_data[str(data[i][0])]["min"] = data[i][4]

    with open('uno/uno_record.json', 'w') as file:
        json.dump(Player_data, file, ensure_ascii=False, indent=2, separators=(',', ': '))
