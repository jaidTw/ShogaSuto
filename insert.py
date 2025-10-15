#!/usr/bin/env python3

from sqlitedict import SqliteDict
import datetime

lvs = [
{'tour': 2, 'location': '兵庫', 'date': datetime.date(2025, 9, 6), 'members': set()},
{'tour': 2, 'location': '兵庫', 'date': datetime.date(2025, 9, 7), 'members': set()},
{'tour': 2, 'location': '愛知', 'date': datetime.date(2025, 9, 20), 'members': set()},
{'tour': 2, 'location': '愛知', 'date': datetime.date(2025, 9, 21), 'members': set()},
{'tour': 2, 'location': '神奈川', 'date': datetime.date(2025, 9, 30), 'members': set()},
{'tour': 2, 'location': '神奈川', 'date': datetime.date(2025, 10, 1), 'members': set()},
{'tour': 3, 'location': '台北', 'date': datetime.date(2025, 8, 10), 'members': set()},
]

with SqliteDict("ztmy.sqlite", tablename="lives", autocommit=True) as lives:
    l = lives[17]
    l['date'] = datetime.date(2025,11,19)
    l['members'] = set()
    lives[17] = l
#    for i, l in enumerate(lvs):
#        lives[25 + i] = l
"""
with SqliteDict("ztmy.sqlite", tablename="tours", autocommit=True) as tours:
    tours[2] = {'name': "ヨルシカ LIVE TOUR 2025「盗作 再演」"}
    tours[3] = {'name': "TOGENASHI TOGEARI Live in TAIPEI「凛音之理」"}
"""
