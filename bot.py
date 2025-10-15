#!/usr/bin/env python3

import discord
import os
import random
import Lives
from random import randint
from datetime import date, timedelta
from discord import app_commands, AllowedMentions
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

async def unwilling_to_speak(ctx):
    if random.randint(0, 199) == 0:
        await ctx.send("我現在不想和你說話😾😾")
        return 1
    return 0

def songs_to_msg(songs):
    return f'```{"\n".join(map(str, songs))}```'

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
    if await unwilling_to_speak(ctx):
        return
        
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
    if await unwilling_to_speak(ctx):
        return

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
    if await unwilling_to_speak(ctx):
        return

    try:
        a = date.fromisoformat(a)
        b = date.fromisoformat(b)
        if b - a > timedelta(days=365):
            raise ValueError
    except ValueError:
        msg = "日期格式錯誤或差距超過365天"
    else:
        songs = songs_in_range(a, b)
        if not any(songs):
            msg = "{a} ~ {b} 之間沒有即將滿週年的歌曲\n"
        else:
            msg = f"{a} ~ {b} 之間滿週年的歌曲有\n"
            msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="today", description="列出今天滿周年的歌曲")
async def today(ctx):
    if await unwilling_to_speak(ctx):
        return

    songs = songs_in_range(date.today(), date.today() + timedelta(days=1))
    if not any(songs):
        msg = "今天沒有滿週年的歌曲\n"
    else:
        msg = "今天滿週年的歌曲有\n"
        msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="week", description="列出未來一週將滿周年的歌曲")
async def week(ctx):
    if await unwilling_to_speak(ctx):
        return

    songs = songs_in_range(date.today(), date.today() + timedelta(days=7))
    if not any(songs):
        msg = "未來一週沒有滿週年的歌曲\n"
    else:
        msg = "未來一週即將滿週年的歌曲有\n"
        msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="month", description="列出未來一個月將滿周年的歌曲")
async def month(ctx):
    if await unwilling_to_speak(ctx):
        return

    songs = songs_in_range(date.today(), date.today() + timedelta(days=30))
    if not any(songs):
        msg = "未來一個月沒有即將滿週年的歌曲\n"
    else:
        msg = "未來一個月即將滿週年的歌曲有\n"
        msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="year", description="列出未來一年將滿周年的歌曲")
async def year(ctx):
    if await unwilling_to_speak(ctx):
        return

    songs = songs_in_range(date.today(), date.today() + timedelta(days=365))
    msg = "未來一年即將滿週年的歌曲有\n"
    msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="next_n", description="列出未來n天將滿周年的歌曲（N<366）")
async def next_n(ctx, n):
    if await unwilling_to_speak(ctx):
        return

    try:
        n = int(n)
        if n > 365:
            raise ValueError
    except ValueError:
        msg = "錯誤：n必須為小於 366 的整數"
    else:
        songs = songs_in_range(date.today(), date.today() + timedelta(days=int(n)))
        if not any(songs):
            msg = f"未來{n}天沒有即將滿週年的歌曲\n"
        else:
            msg = f"未來{n}天即將滿週年的歌曲有\n"
            msg += songs_to_msg(songs)
    await ctx.send(msg)

@bot.hybrid_command(name="poke", description="戳戳")
async def poke(ctx):
    song = random_song()
    msg = f"掉落了**{song.name}**\n{song.url}"
    await ctx.send(msg)

@bot.hybrid_command(name="seat", description="抽位子")
async def seat(ctx):
    msg = random_seat()
    await ctx.send(msg)
@bot.hybrid_command(name="attend", description="參加")
async def attend(ctx, tour="", date=""):
    if tour == "":
        msg = Lives.list_tours()
    elif date == "":
        msg = Lives.list_lives(tour)
    else:
        if Lives.reg_attend(tour, date, ctx.guild.id, ctx.author.id):
            msg = f"發生錯誤，請確認參數是否正確"
        else:
            msg = f"**{ctx.author.mention}**已註冊參加{date}的公演"
    await ctx.send(msg, allowed_mentions=AllowedMentions.none())

@bot.hybrid_command(name="unattend", description="取消參加")
async def unattend(ctx, tour="", date=""):
    if tour == "":
        msg = Lives.list_tours()
    elif date == "":
        msg = Lives.list_lives(tour)
    else:
        if Lives.unreg_attend(tour, date, ctx.guild.id, ctx.author.id):
            msg = f"發生錯誤，請確認參數是否正確"
        else:
            msg = f"**{ctx.author.mention}**已取消參加{date}的公演"
    await ctx.send(msg, allowed_mentions=AllowedMentions.none())

@bot.hybrid_command(name="attendee", description="查詢參加者")
async def attendee(ctx, tour="", date=""):
    await ctx.defer()
    if tour == "":
        msg = Lives.list_tours()
    elif date == "":
        lives = Lives.list_tour_attendees(tour)
        if not(lives):
            msg = f"發生錯誤，請確認參數是否正確"
        else:
            tour_name = Lives.get_tour_name(tour)
            msg = f"**{tour_name}** 的參加者：\n\n"
            for live in lives:
                attendees = []
                for gid, uid in live['members']:
                    if gid == ctx.guild.id:
                        mem = await ctx.guild.fetch_member(uid)
                        attendees.append(mem.mention)
                msg += f"{live['date'].strftime('%m/%d')} {live['location']}：" + "、".join(attendees) + "\n"
    else:
        lives = Lives.list_attend(tour, date)
        if not(lives):
            msg = f"發生錯誤，請確認參數是否正確"
        else:
            msg = ""
            for live in lives:
                attendees = []
                tour_name = Lives.get_tour_name(tour)
                msg += f"{tour_name} {live['date'].strftime('%m/%d')} {live['location']} 的參加者：\n"
                for gid, uid in live['members']:
                    if gid == ctx.guild.id:
                        mem = await ctx.guild.fetch_member(uid)
                        attendees.append(mem.mention)
                if any(attendees):
                    msg += "、".join(attendees) + "\n"
                else:
                    msg += "無\n"
    await ctx.send(msg, allowed_mentions=AllowedMentions.none())

bot.run(TOKEN)
