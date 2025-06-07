#!/usr/bin/env python3

import discord
import os
import random
from random import randint
from datetime import date, timedelta
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from songs import songs_in_range, random_song

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = int(os.getenv('DISCORD_CHANNEL'))

LANG = 'zh_TW'
GUILD_ID = discord.Object(id=1295405688616652884)

intents = discord.Intents.default()
intents.message_content = True

random.seed()
bot = commands.Bot(command_prefix='/', intents=intents)

def dont_want_to_speak():
    if random.randint(0, 1000) == 0:
        return True
    return False

def songs_to_msg(songs):
    msg = f'```{"\n".join(map(str, songs))}```'
    return msg

"""
Event Loop:
"""
@bot.event
async def on_ready():
    slash = await bot.tree.sync()
    print(f"Logged in with user {bot.user}")
    print(f"{len(slash)} slash commands loaded")

@bot.hybrid_command(name="myname", description="顯示生姜現在或在某個日期(d=YYYY-MM-DD)時的名字")
async def name(ctx, d=None):
    if dont_want_to_speak():
        await ctx.send("現在不想和你說話")
        
    msg = "我現在的名字是「**アポ取りしょうがストリングス**」"
    if d != None:
        try:
            d = date.fromisoformat(d)
        except ValueError:
            pass
        else:
            if d < date(2021, 4, 5):
                msg = f"我在{d}時還沒誕生"
            elif date(2021, 4, 5) < d <= date(2022, 4, 5):
                msg = f"我在{d}時的名字是「**新生姜ストリングス**」"
            elif date(2022, 4, 5) < d <= date(2022, 9, 1):
                msg = f"我在{d}時的名字是「**真・しょうがストリングス**」"
            elif date(2022, 9, 1) < d <= date(2023, 4, 5):
                msg = f"我在{d}時的名字是「**家系・しょうがストリングス**」"
            elif date(2023, 4, 5) < d <= date(2024, 4, 5):
                msg = f"我在{d}時的名字是「**SASUKE・しょうがストリングス**」"
            elif date(2024, 4, 5) < d <= date(2025, 4, 5):
                msg = f"我在{d}時的名字是「**パッド・パウエルしょうがストリングス**」"
            elif date(2025, 4, 5) < d:
                msg = f"我在{d}時的名字是「**アポ取りしょうがストリングス**」"
    await ctx.send(msg)

@bot.hybrid_command(name="chronical", description="顯示生姜的生涯事紀")
async def chronical(ctx, d=None):
    if dont_want_to_speak():
        await ctx.send("現在不想和你說話")

    msg = f"我的貓生\n"
    msg += f"2021-04-05 誕生，名字是「**新生姜ストリングス**」\n"
    msg += f"2022-04-05 改名「**真・しょうがストリングス**」\n"
    msg += f"2022-09-01 改名「**家系・しょうがストリングス**」\n"
    msg += f"2023-04-05 改名「**SASUKE・しょうがストリングス**」\n"
    msg += f"2024-04-05 改名「**パッド・パウエルしょうがストリングス**」\n"
    msg += f"2025-04-05 改名「**アポ取りしょうがストリングス**」\n"
    await ctx.send(msg)

@bot.hybrid_command(name="interval", description="列出日期[a, b)之間滿週年的歌曲，格式為YYYY-MM-DD且間隔不能大於365天")
async def interval(ctx, a, b):
    if dont_want_to_speak():
        await ctx.send("現在不想和你說話")

    try:
        a = date.fromisoformat(a)
        b = date.fromisoformat(b)
        if b - a > timedelta(days=365):
            raise ValueError
    except ValueError:
        msg = "日期格式錯誤或差距超過365天"
    else:
        songs = songs_in_range(a, b)
        msg = f"{a} ~ {b} 之間滿週年的歌曲有\n"
        msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="today", description="列出今天滿周年的歌曲")
async def today(ctx):
    if dont_want_to_speak():
        await ctx.send("現在不想和你說話")

    songs = songs_in_range(date.today(), date.today() + timedelta(days=1))
    if not any(songs):
        msg = "今天沒有滿週年的歌曲\n"
    else:
        msg = "今天滿週年的歌曲有\n"
        msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="week", description="列出未來一週將滿周年的歌曲")
async def week(ctx):
    if dont_want_to_speak():
        await ctx.send("現在不想和你說話")

    songs = songs_in_range(date.today(), date.today() + timedelta(days=7))
    msg = "未來一週即將滿週年的歌曲有\n"
    msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="month", description="列出未來一個月將滿周年的歌曲")
async def month(ctx):
    if dont_want_to_speak():
        await ctx.send("現在不想和你說話")

    songs = songs_in_range(date.today(), date.today() + timedelta(days=30))
    msg = "未來一個月即將滿週年的歌曲有\n"
    msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="year", description="列出未來一年將滿周年的歌曲")
async def year(ctx):
    if dont_want_to_speak():
        await ctx.send("現在不想和你說話")

    songs = songs_in_range(date.today(), date.today() + timedelta(days=365))
    msg = "未來一年即將滿週年的歌曲有\n"
    msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="next_n", description="列出未來n天將滿周年的歌曲（N<366）")
async def next_n(ctx, n):
    if dont_want_to_speak():
        await ctx.send("現在不想和你說話")

    try:
        n = int(n)
        if n > 365:
            raise ValueError
    except ValueError:
        msg = "錯誤：n必須為小於 366 的整數"
    else:
        songs = songs_in_range(date.today(), date.today() + timedelta(days=int(n)))
        msg = f"未來{n}天即將滿週年的歌曲有\n"
        msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="poke", description="戳戳")
async def poke(ctx):
    song = random_song()
    msg = f"掉落了**{song.name}**\n{song.url}"
    await ctx.send(msg)

bot.run(TOKEN)
