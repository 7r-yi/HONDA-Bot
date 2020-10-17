import json

with open('zyanken_record.json', 'r') as f:
    data = json.load(f)

#data[str(4)] = {"win": {"グー": 0, "チョキ": 0, "パー": 0}, "lose": {"グー": 0, "チョキ": 0, "パー": 0}}
print(list(data["514787948579913748"]["win"].values()))