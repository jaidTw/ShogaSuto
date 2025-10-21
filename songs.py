from datetime import date, timedelta
from songList import SONGS_with_MV, SONGS_all, SONGS_live
import random

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

def random_song_legacy():
    if random.randint(0, 99) < 2:
        return Song("2009-10-25", "Never Gonna Give You Up", "", "dQw4w9WgXcQ")
    return random.choice(songs)

songs_all = []
songs_live = []

for k, v in SONGS_all.items():
    date = date.fromisoformat(k)
    songs.append(Song(date, *v))

for k, v in SONGS_live.items():
    date = date.fromisoformat(k)
    songs.append(Song(date, *v))

def random_song():
    if random.randint(0, 99) < 2:
        return Song("2009-10-25", "Never Gonna Give You Up", "", "dQw4w9WgXcQ")
    return random.choice(songs_all)

def random_song_live():
    if random.randint(0, 99) < 2:
        return Song("2009-10-25", "Never Gonna Give You Up", "", "dQw4w9WgXcQ")
    return random.choice(songs_live)

def random_seat():
    level = random.randint(1, 3)
    if random.randint(0, 99) < 5
        level = 7

    row = random.randint(1, 30)
    number = random.randint(1, 60)    
    return f"你抽到的位子是{level}階{row}列{number}番"

