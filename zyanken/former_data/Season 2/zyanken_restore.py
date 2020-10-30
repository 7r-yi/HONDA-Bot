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
    flag = 0
    for reaction in reactions:
        if reaction.me and reaction.emoji == "🎉":
            flag = 1
            break
        elif reaction.me and reaction.emoji == "👎":
            flag = 2
            break

    return flag


def check_win(reactions, word):
    flag = False
    for reaction in reactions:
        if reaction.me and reaction.emoji == "🎉":
            flag = True
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
        return my, honda, "lose", "win"


def data_restore(messages):
    data = constant.zyanken_data
    for message in messages:
        key = check_reaction(message.reactions)
        if key in [1, 2]:
            word = jaconv.hira2kata(jaconv.h2z(message.content))
            if "グー" in word:
                my, honda, my_rslt, honda_rslt = check_win(message.reactions, word)
            elif "チョキ" in word:
                my, honda, my_rslt, honda_rslt = check_win(message.reactions, word)
            else:
                my, honda, my_rslt, honda_rslt = check_win(message.reactions, word)
            if str(message.author.id) not in data:
                data[str(message.author.id)] = {"win": {"r": 0, "s": 0, "p": 0}, "lose": {"r": 0, "s": 0, "p": 0},
                                                "keep": {"cnt": 0, "max": 0}}
            data[str(message.author.id)][my_rslt][my] += 1
            data[str(constant.Honda)][honda_rslt][honda] += 1
            if key == 1:
                data[str(message.author.id)]["keep"]["cnt"] += 1
                if data[str(message.author.id)]["keep"]["cnt"] > data[str(message.author.id)]["keep"]["max"]:
                    data[str(message.author.id)]["keep"]["max"] = data[str(message.author.id)]["keep"]["cnt"]
                data[str(constant.Honda)]["keep"]["cnt"] = 0
            else:
                data[str(message.author.id)]["keep"]["cnt"] = 0
                data[str(constant.Honda)]["keep"]["cnt"] += 1
                if data[str(constant.Honda)]["keep"]["cnt"] > data[str(constant.Honda)]["keep"]["max"]:
                    data[str(constant.Honda)]["keep"]["max"] = data[str(constant.Honda)]["keep"]["cnt"]
    constant.zyanken_data = data
    with open('zyanken/zyanken_record.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))


"""
    boot_time = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
    bot_msgs = await client.get_channel(constant.Test_room).history(limit=30).flatten()
    for msg in bot_msgs:
        if "Data input" in msg.content:
            time = datetime.strptime(msg.content.split("\n")[0], '%Y/%m/%d %H:%M:%S') - timedelta(hours=9)
            msgs = await client.get_channel(constant.Zyanken_room).history(limit=None, after=time) \
                .filter(lambda m: zyanken_restore.check_hand(m)).flatten()
            zyanken_restore.data_restore(msgs)
            await client.get_channel(constant.Test_room).send(
                f"{boot_time}\nBooted", file=discord.File('zyanken/zyanken_record.json'))
            break
    """
