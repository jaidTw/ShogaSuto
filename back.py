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
    ("大阪團子轉盤帥保背", "https://i.imgur.com/kRClWQC.jpeg"),
    ("昕家保背", "https://i.imgur.com/eFOrHHj.jpeg"),
    ("南港保背 (ft. 鳥背)", "https://i.imgur.com/OU7mOLD.jpeg"),
    ("台南拉風保背", "https://i.imgur.com/lSLE99m.jpeg"),
    ("野餐保背", "https://i.imgur.com/sDMISMU.jpeg"),
    ("一心炭數碼保背", "https://i.imgur.com/KVxhI3S.jpeg"),
    ("仰望上野動物園保背", "https://i.imgur.com/hH8v58y.jpeg"),
    ("仰望上野動物園保背(ft. Shampoo背)", "https://i.imgur.com/Dyerwc1.jpeg"),
    ("收蘋果佬禮物保背", "https://i.imgur.com/jtRCgYV.jpeg"),
    ("武道館聖光保背", "https://i.imgur.com/Xf9tB0z.jpeg"),
    ("武道館P席滑手機保背", "https://i.imgur.com/EK5KqWF.jpeg"),
    ("飽貝 (ft. Shampoo背)", "https://i.imgur.com/EHxIaP5.jpeg"),
    ("親簽保背拍", "https://i.imgur.com/DaaD5Ht.jpeg"),
    ("UR愛翔馬保背", "https://i.imgur.com/eNTnJ42.jpeg"),
]

def paulback():
    index = random.randint(0, len(BACKS) - 1)
    name, url = BACKS[index]

    return f"你抽到了{name}：{url}"

