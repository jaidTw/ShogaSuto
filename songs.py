from datetime import date, timedelta

SONGS = {
    "2019-02-04" : "眩しいDNAだけ",
    "2019-10-08" : "こんなこと騒動",
    "2019-10-18" : "ハゼ馳せる果てるまで",
    "2021-01-20" : "暗く黒く",
    "2021-02-10" : "胸の煙",
    "2022-02-16" : "袖のキルト",
    "2025-02-28" : "シェードの埃は延長",
    "2021-03-30" : "勘冴えて悔しいわ",
    "2022-04-07" : "ミラーチューン",
    "2025-04-18" : "微熱魔",
    "2019-05-08" : "正義",
    "2020-05-14" : "お勉強しといてよ",
    "2023-05-15" : "不法侵入",
    "2025-05-22" : "クリームで会いにいけますか",
    "2024-05-23" : "嘘じゃない",
    "2018-06-04" : "秒針を噛む",
    "2023-06-04" : "花一匁",
    "2021-06-08" : "あいつら全員同窓会",
    "2021-07-04" : "ばかじゃないのに",
    "2020-07-13" : "MILABO",
    "2020-07-23" : "低血ボルト",
    "2020-08-11" : "Ham",
    "2020-12-17" : "正しくなれない",
    "2022-09-15" : "夏枯れ",
    "2019-09-26" : "蹴っ飛ばした毛布",
    "2018-10-02" : "脳裏上のクラッカー",
    "2018-11-06" : "ヒューマノイド",
    "2019-10-29" : "Dear Mr. 「F」",
    "2020-12-01" : "勘ぐれい",
    "2021-12-02" : "猫リセット",
    "2022-10-20" : "残機",
    "2022-12-15" : "綺羅キラー",
    "2024-06-06" : "Blues in the Closet",
    "2024-08-29" : "海馬成長痛",
    "2024-10-23" : "クズリ念",
    "2024-12-05" : "TAIDADA",
    "2025-06-12" : "形",
}

songs = dict()

for k, v in SONGS.items():
    date = date.fromisoformat(k)
    songs[date] = v

class QueryResult:
    def __init__(self, name, date, adjusted_date):
        self.name = name
        self.date = date
        self.adjusted_date = adjusted_date

def songs_in_range(begin, end):
    if end - begin > timedelta(days=365):
        return []

    anniv_songs = []
    for date, name in songs.items():
        adjusted_date = date.replace(year=begin.year)
        if (date.month < begin.month) or (date.month == begin.month and date.day < begin.day):
            adjusted_date = adjusted_date.replace(year=begin.year+1)

        if begin <= adjusted_date < end:
            if adjusted_date.year - date.year == 0:
                continue
            anniv_songs.append((name, date, adjusted_date, adjusted_date.year-date.year))

    anniv_songs.sort(key=lambda x: (x[2]-date.today(), x[3]*-1))
    return anniv_songs

