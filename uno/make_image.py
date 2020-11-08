from uno import uno


def id_to_pass(id):
    if 100 <= id < 200:
        return f"./image/Red_{id % 100}"
    elif 200 <= id < 300:
        return f"./image/Blue_{id % 200}"
    elif 300 <= id < 400:
        return f"./image/Green_{id % 300}"
    elif 400 <= id < 500:
        return f"./image/Yellow_{id % 400}"
    else:
        return f"./image/Black_{id % 500}"


def make_hand(card):
    for i in card:
        id_to_pass(uno.card_to_id(i))