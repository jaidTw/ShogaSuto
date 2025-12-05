import random

BACKS = [
    ("日K保背", "https://i.imgur.com/UCxwOHV.jpeg"),
    ("丹尼保背", "https://i.imgur.com/5MrRxHP.jpeg"),
    ("革蟬展保背", "https://i.imgur.com/wdexinF.jpeg"),
    ("萬博保背", "https://i.imgur.com/Oo4hjql.jpeg"),
    ("生日保背背", "https://i.imgur.com/xa9pytU.jpeg"),
    ("神戶電扶梯保背", "https://i.imgur.com/eNtrJy3.jpeg"),
    ("品川新幹線行囊保背", "https://i.imgur.com/Di0u6oN.jpeg"),
    ("鐵板野郎保背", "https://i.imgur.com/40tkWYB.png"),
    ("大阪團子轉盤帥保背", "https://i.imgur.com/kRClWQC.jpeg")
]

def paulback():
    index = random.randint(0, len(BACKS) - 1)
    name, url = BACKS[index]

    return f"你抽到了{name}：{url}"

