import json
import jaconv
import constant


def check_hand(message):
    if "グー" in jaconv.hira2kata(jaconv.h2z(message.content)) and not message.author.bot:
        return True
    elif "チョキ" in jaconv.hira2kata(jaconv.h2z(message.content)) and not message.author.bot:
        return True
    elif "パー" in jaconv.hira2kata(jaconv.h2z(message.content)) and not message.author.bot:
        return True
    else:
        return False


def check_reaction(reactions):
    flag = False
    for reaction in reactions:
        if reaction.me and (reaction.emoji == "🎉" or reaction.emoji == "👎"):
            flag = True
            break

    return flag


def check_win(reactions, word):
    flag, loop = False, True
    for reaction in reactions:
        if reaction.me and reaction.emoji == "🎉":
            flag = True
            break
        else:
            flag = False
            break

    if flag:
        if "グー" in word:
            my, honda = "r", "s"
        elif "チョキ" in word:
            my, honda = "s", "p"
        else:
            my, honda = "p", "r"
        return my, honda, "win", "lose"
    else:
        if "グー" in word:
            my, honda = "r", "p"
        elif "チョキ" in word:
            my, honda = "s", "r"
        else:
            my, honda = "p", "s"
        return my, honda,  "lose", "win"


def data_restore(messages):
    data = constant.zyanken_data
    for message in messages:
        if check_reaction(message.reactions):
            word = jaconv.hira2kata(jaconv.h2z(message.content))
            if "グー" in word:
                my, honda, my_rslt, honda_rslt = check_win(message.reactions, word)
            elif "チョキ" in word:
                my, honda, my_rslt, honda_rslt = check_win(message.reactions, word)
            else:
                my, honda, my_rslt, honda_rslt = check_win(message.reactions, word)
            if str(message.author.id) not in data:
                data[str(message.author.id)] = {"win": {"r": 0, "s": 0, "p": 0}, "lose": {"r": 0, "s": 0, "p": 0},
                                                "keep": {"flag": 0, "cnt": 0, "max": 0}}
            data[str(message.author.id)][my_rslt][my] += 1
            data[str(constant.Honda)][honda_rslt][honda] += 1
    constant.zyanken_data = data
    with open('zyanken/zyanken_record.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
