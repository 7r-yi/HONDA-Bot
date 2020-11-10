import json
from uno import uno_func

with open('uno/uno_record.json', 'r') as f:
    Player_data = json.load(f)


def add_penalty(player):
    if str(player) not in Player_data:
        Player_data[str(player)] = {"win": 0, "lose": 0, "point": 0, "max": 0, "min": 0, "penalty": 0}
    Player_data[str(player)]["point"] -= 300
    Player_data[str(player)]["penalty"] += 1


def data_save(data):
    for i in range(len(data)):
        if str(data[i][0]) not in Player_data:
            Player_data[str(data[i][0])] = {"win": 0, "lose": 0, "point": 0, "max": 0, "min": 0, "penalty": 0}
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


def record_output(id):
    data = list(Player_data[str(id)].values())
    win_rate = round(data[0] / (data[0] + data[1]) * 100, 2)

    if data[2] < 0:
        url = 'https://i.imgur.com/adtGl7h.png'  # YOU LOSE
    else:
        url = 'https://i.imgur.com/1JXc9eD.png'  # YOU WIN

    return [data[0], data[1], win_rate, data[2], data[3], data[4], data[5], url]
