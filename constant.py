import json

Joiner = []
Question = {}
Answer = {}
Former_winner_wins = None
Former_winner_rate = None
Former_loser_rate = None
with open('zyanken_record.json', 'r') as f:
    zyanken_data = json.load(f)

Shichi = 193407417256640512
Honda = 359330668112642059
Server = 764419309610598420
System = 766243950087897109
Welcome = 765164785443930134
Gate = 765950697572663317
Recruit = 765164299777605643
Quiz_room = 766006209236303933
Zyanken_room = 766963547770716182
Winner_room = 766038908789456917
Test_room = 766114833208180736
Administrator = 764430231444127744
Participant = 764991717006639114
Winner = 765968517161025538
Loser = 768056812317966337
Visitor = 765155244161105930
