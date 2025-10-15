from datetime import date, timedelta
import random

SONGS = {
    "2018-06-04" : ("秒針を噛む",                 "Byoushinwo Kamu",        "GJI4Gv7NbmE"),
    "2018-10-02" : ("脳裏上のクラッカー",         "Nouriueno Cracker",      "3iAXclHlTTg"),
    "2018-11-06" : ("ヒューマノイド",             "Humanoid",               "GAB26GgJ8V8"),
    "2019-02-04" : ("眩しいDNAだけ",              "Mabushii DNA Dake",      "VJy8qZ77bpE"),
    "2019-05-08" : ("正義",                       "Seigi",                  "7kUbX4DoZoc"),
    "2019-09-26" : ("蹴っ飛ばした毛布",           "Kettobashita Moufu",     "iyCRK5WfFOI"),
    "2019-10-08" : ("こんなこと騒動",             "Konnakoto Soudou",       "mlA-Z7zSLHU"),
    "2019-10-18" : ("ハゼ馳せる果てるまで",       "Haze Haseru Haterumade", "ElnxZtiBDvs"),
    "2019-10-29" : ("Dear Mr 「F」",              "Dear. Mr\"F\"",          "Qw-FSw7d2zE"),
    "2020-05-14" : ("お勉強しといてよ",           "Study Me",               "Atvsg_zogxo"),
    "2020-07-13" : ("MILABO",                     "MILABO",                 "I88PrE-KUPk"),
    "2020-07-23" : ("低血ボルト",                 "Fastening",              "COll6PdtI5w"),
    "2020-08-11" : ("Ham",                        "Ham",                    "ouLndhBRL4w"),
    "2020-12-01" : ("勘ぐれい",                   "Hunch Gray",             "ugpywe34_30"),
    "2020-12-17" : ("正しくなれない",             "Can't be right",         "258qUAI7rck"),
    "2021-01-20" : ("暗く黒く",                   "Darken",                 "dcOwj-QE_ZE"),
    "2021-02-10" : ("胸の煙",                     "One's Mind",             "wQPgM-9LatM"),
    "2021-03-30" : ("勘冴えて悔しいわ",           "Kan Saete Kuyashiiwa",   "4QePrv24TBU"),
    "2021-06-08" : ("あいつら全員同窓会",         "Inside Joke",            "ZUwaudw8ht0"),
    "2021-07-04" : ("ばかじゃないのに",           "Stay Foolish",           "YgmFIVOR1-I"),
    "2021-12-02" : ("猫リセット",                 "Neko Reset",             "Sfz5TpCRSiI"),
    "2022-02-16" : ("袖のキルト",                 "Quilt",                  "9PnCSI8ndws"),
    "2022-04-07" : ("ミラーチューン",             "Mirror Tune",            "BVvvUGP0MFw"),
    "2022-09-08" : ("消えてしまいそうです",       "Blush",                  "OxcnK1s2Fww"),
    "2022-09-15" : ("夏枯れ",                     "Summer Slack",           "Nmemc-b6cdU"),
    "2022-10-20" : ("残機",                       "Time Left",              "6OC92oxs4gA"),
    "2022-12-15" : ("綺羅キラー",                 "Kira Killer",            "e5LaKxJVeVI"),
    "2023-05-15" : ("不法侵入",                   "Intrusion",              "SAdkxVFyAyc"),
    "2023-06-04" : ("花一匁",                     "Hanaichi Monnme",        "H88kps8X4Mk"),
    "2024-05-23" : ("嘘じゃない",                 "Truth in Lies",          "GfDXqY-V0EY"),
    "2024-06-06" : ("Blues in the Closet",        "Blues in the Closet",    "E8RMWLoAsa0"),
    "2024-08-29" : ("海馬成長痛",                 "Hippocampal Pain",       "PLG2Uexyi9s"),
    "2024-10-23" : ("クズリ念",                   "KUZURI",                 "ut889MZ9yNo"),
    "2024-12-05" : ("TAIDADA",                    "TAIDADA",                "IeyCdm9WwXM"),
    "2025-02-28" : ("シェードの埃は延長",         "SHADE",                  "zjEMFuj23B4"),
    "2025-04-18" : ("微熱魔",                     "Warmthaholic",           "plpVOHqh3lA"),
    "2025-05-22" : ("クリームで会いにいけますか", "CREAM",                  "JQ2913bVo30"),
#    "2025-06-12" : ("形",                         "Pain Give Form",         None),
}

class Song:
    def __init__(self, d, name, en_name, mv):
        self.date = d
        self.name = name
        self.en_name = en_name
        self.mv = mv

    @property
    def year(self):
        return self.date.year

    @property
    def month(self):
        return self.date.month

    @property
    def day(self):
        return self.date.day

    @property
    def url(self):
        return f"https://youtu.be/{self.mv}"

    # Adjusted the year for easier date range checking
    # We adjust dates that earlier than the basis to next year, and dates that
    # later than the basis to the same year, so that every adjusted date is in
    # the next 365 days of the basis
    def adjusted_date(self, basis):
        if (self.month < basis.month) or (self.month == basis.month and self.day < basis.day):
            return self.date.replace(year=basis.year+1)
        else:
            return self.date.replace(year=basis.year)

    def __str__(self):
        return f"{self.date}\t{self.name}"

random.seed()
songs = []

for k, v in SONGS.items():
    date = date.fromisoformat(k)
    songs.append(Song(date, *v))

class QueryResult(Song):
    def __init__(self, d, name, en_name, mv, adj_date):
        super().__init__(d, name, en_name, mv)
        self.adj_date = adj_date
        self.anniv = adj_date.year - d.year

    @classmethod
    def from_song(cls, song, adj_date):
        return cls(song.date, song.name, song.en_name, song.mv, adj_date)

    def __str__(self):
        return f"{self.date}\t{self.anniv}週年\t{self.name}"

def songs_in_range(begin, end):
    if end - begin > timedelta(days=365):
        return []

    anniv_songs = []
    for song in songs:
        adj_date = song.adjusted_date(begin)
        if begin <= adj_date < end:
            anniv_songs.append(QueryResult.from_song(song, adj_date))

    anniv_songs.sort(key=lambda x: (x.adj_date - date.today(), x.anniv*-1))
    return anniv_songs

def random_song():
    if random.randint(0, 99) < 3:
        return Song("2009-10-25", "Never Gonna Give You Up", "", "dQw4w9WgXcQ")
    return random.choice(songs)

def random_seat():
    level = random.randint(1, 3)
    if random.randint(0, 99) < 5
        level = 7

    row = random.randint(1, 3)
    number = random.randint(1, 3)    
    return f"你抽到的位子是{level}階{row}列{number}番"

