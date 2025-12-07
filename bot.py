#!/usr/bin/env python3

import discord
import os
import random
import asyncio
from random import randint
import datetime
from datetime import date, timedelta
from discord import app_commands, AllowedMentions
from discord.ext import commands, tasks
from dotenv import load_dotenv
from songs import songs_in_range, random_song, random_seat
from back import paulback
from ticketjam import TicketDatabase, mark_tickets_as_posted, TicketJamScraper

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = int(os.getenv('DISCORD_CHANNEL'))
TICKET_CHANNEL = int(os.getenv('TICKET_CHANNEL'))
BIRTHDAY_CHANNEL = int(os.getenv('BIRTHDAY_CHANNEL'))
SCRAPE_URL = os.getenv('SCRAPE_URL', 'https://ticketjam.jp/tickets/zuttomayonakade-iinoni?sort_query%5BisSellable%5D=true')

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

def format_ticket_for_discord(ticket):
    """Format a ticket for Discord posting with price change information"""
    # Use TicketDatabase to get enhanced ticket info with price changes
    db = TicketDatabase()
    enhanced_ticket = db.get_ticket_with_price_info(ticket)

    # Map color hints to Discord colors
    color_map = {
        'default': 0x00ff00,    # Green
        'increase': 0xff6b6b,   # Red for price increase
        'decrease': 0x51cf66    # Bright green for price decrease
    }
    color = color_map.get(enhanced_ticket['color_hint'], 0x00ff00)

    embed = discord.Embed(
        title=f"🎫 {ticket['event_name'][:100]}",
        url=ticket['url'],
        color=color,
        description=f"**価格:** {enhanced_ticket['price_info']}\n**枚数:** {ticket['quantity']}"
    )

    # Add fields
    if ticket['date']:
        embed.add_field(name="📅 日付", value=ticket['date'], inline=True)
    if ticket['time']:
        embed.add_field(name="🕐 時間", value=ticket['time'], inline=True)
    if ticket['venue']:
        embed.add_field(name="🏢 会場", value=ticket['venue'], inline=True)
    if ticket['location']:
        embed.add_field(name="📍 場所", value=ticket['location'], inline=True)
    if ticket['seat_info']:
        embed.add_field(name="💺 座席", value=ticket['seat_info'], inline=True)
    if ticket['days_remaining']:
        embed.add_field(name="⏰ 残り", value=ticket['days_remaining'], inline=True)

    # Add instant buy indicator
    if ticket['is_instant_buy']:
        embed.add_field(name="⚡", value="即決可能", inline=True)

    # Add price change history if there are multiple prices
    price_history = enhanced_ticket['price_history']
    if len(price_history) > 2:
        history_text = []
        for i, entry in enumerate(price_history[-3:]):  # Show last 3 entries
            timestamp = entry['recorded_at'][:10]  # Just the date part
            history_text.append(f"{timestamp}: {entry['price']}")

        embed.add_field(
            name="📊 価格履歴",
            value="\n".join(history_text),
            inline=False
        )

    # Add footer with ticket ID
    embed.set_footer(text=f"Ticket ID: {ticket['ticket_id'][:8]}...")

    return embed

async def post_tickets():
    """Post all unposted tickets to the Discord channel"""
    try:
        db = TicketDatabase()
        unposted_tickets = db.get_unposted_tickets('active')  # Only active tickets

        if not unposted_tickets:
            return {"status": "success", "message": "No unposted tickets found", "count": 0}

        channel = bot.get_channel(TICKET_CHANNEL)
        if not channel:
            print(f"Could not find channel with ID {TICKET_CHANNEL}")
            return {"status": "error", "message": f"Could not find channel with ID {TICKET_CHANNEL}"}

        posted_count = 0
        ticket_ids_to_mark = []

        # Post each ticket
        for ticket in unposted_tickets:
            try:
                embed = format_ticket_for_discord(ticket)
                await channel.send(embed=embed)
                ticket_ids_to_mark.append(ticket['ticket_id'])
                posted_count += 1

                # Add small delay to avoid rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                print(f"Error posting ticket {ticket['ticket_id']}: {e}")
                continue

        # Mark posted tickets as posted
        if ticket_ids_to_mark:
            mark_tickets_as_posted(ticket_ids_to_mark)
            print(f"Successfully posted {posted_count} tickets and marked them as posted")

        return {
            "status": "success",
            "message": f"Posted {posted_count} tickets",
            "count": posted_count,
            "ticket_ids": ticket_ids_to_mark
        }

    except Exception as e:
        print(f"Error in post_tickets: {e}")
        return {"status": "error", "message": str(e)}

TRIGGER_TIME = datetime.time(hour=1, minute=0, tzinfo=datetime.timezone.utc)
@tasks.loop(time=TRIGGER_TIME)
async def post_anniv():
    """Post anniversary songs on 9AM UTC+8 every day"""
    songs = songs_in_range(date.today(), date.today() + timedelta(days=1))
    if not any(songs):
        return jsonify({"status": "success"})

    channel = bot.get_channel(BIRTHDAY_CHANNEL)
    try:
        for song in songs:
            year = date.today().year - song.year
            string = f"今天是**{song.name}**的 {year} 歲生日，生日快樂 :tada: :tada:！\n{song.url}"
            await channel.send(string)

            # Add small delay to avoid rate limiting
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error in post_anniv: {e}")
        return {"status": "error", "message": str(e)}

    return result

@tasks.loop(minutes=5)
async def scrape_tickets():
    """Scrape tickets every 5 minutes"""
    try:
        print("🔍 Starting scheduled ticket scraping...")
        scraper = TicketJamScraper()

        # Scrape tickets from the configured URL
        tickets = scraper.scrape_tickets(SCRAPE_URL)

        if not tickets:
            print("No tickets found during scraping")
            return

        # Update database
        new_count = 0
        updated_count = 0
        price_changes = []
        current_ticket_ids = []

        for ticket in tickets:
            is_new, action = scraper.db.insert_or_update_ticket(ticket)
            current_ticket_ids.append(ticket.ticket_id)

            if is_new:
                new_count += 1
            elif "Price changed" in action:
                # Only count as updated if something actually changed (price change)
                updated_count += 1
                price_changes.append((ticket, action))
            # If action is just "Updated last_seen", don't count as updated

        # Delete removed tickets (tickets that are no longer available)
        deleted_count = scraper.db.delete_removed_tickets(current_ticket_ids)

        print(f"✅ Scraping completed: New: {new_count}, Updated: {updated_count}, Deleted: {deleted_count}, Price changes: {len(price_changes)}")

        # If there are new tickets or price changes, they will be posted by the post_tickets task

    except Exception as e:
        print(f"❌ Error in scheduled scraping: {e}")
    await post_tickets()

@post_anniv.before_loop
async def before_anniv():
    await bot.wait_until_ready()

@scrape_tickets.before_loop
async def before_scrape_tickets():
    await bot.wait_until_ready()

async def post_unposted_tickets():
    """Post all unposted tickets to Discord channel"""
    try:
        db = TicketDatabase()
        unposted_tickets = db.get_unposted_tickets('active')

        if not unposted_tickets:
            return {"status": "success", "message": "No unposted tickets found", "count": 0}

        channel = bot.get_channel(CHANNEL)
        if not channel:
            return {"status": "error", "message": f"Could not find channel with ID {CHANNEL}"}

        posted_count = 0
        ticket_ids_to_mark = []

        for ticket in unposted_tickets:
            try:
                embed = format_ticket_for_discord(ticket)
                await channel.send(embed=embed)
                ticket_ids_to_mark.append(ticket['ticket_id'])
                posted_count += 1

                # Add small delay to avoid rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                print(f"Error posting ticket {ticket['ticket_id']}: {e}")
                continue

        # Mark all successfully posted tickets as posted
        if ticket_ids_to_mark:
            mark_tickets_as_posted(ticket_ids_to_mark)

        return {
            "status": "success",
            "message": f"Posted {posted_count} tickets",
            "count": posted_count,
            "ticket_ids": ticket_ids_to_mark
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

async def manual_scrape():
    """Manual scraping triggered via Discord command"""
    try:
        print("🔍 Manual scraping triggered via Discord command...")
        scraper = TicketJamScraper()

        tickets = scraper.scrape_tickets(SCRAPE_URL)

        if not tickets:
            return {"status": "success", "message": "No tickets found", "count": 0}

        new_count = 0
        updated_count = 0
        price_changes = []
        current_ticket_ids = []

        for ticket in tickets:
            is_new, action = scraper.db.insert_or_update_ticket(ticket)
            current_ticket_ids.append(ticket.ticket_id)

            if is_new:
                new_count += 1
            elif "Price changed" in action:
                # Only count as updated if something actually changed (price change)
                updated_count += 1
                price_changes.append((ticket, action))
            # If action is just "Updated last_seen", don't count as updated

        deleted_count = scraper.db.delete_removed_tickets(current_ticket_ids)

        return {
            "status": "success",
            "message": f"Scraping completed",
            "new_tickets": new_count,
            "updated_tickets": updated_count,
            "deleted_tickets": deleted_count,
            "price_changes": len(price_changes)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

"""
Event Loop:
"""
@bot.event
async def on_ready():
    slash = await bot.tree.sync()
    print(f"Logged in with user {bot.user}")
    print(f"{len(slash)} slash commands loaded")

    # Start scheduled tasks
    if not post_anniv.is_running():
        post_anniv.start()
    if not scrape_tickets.is_running():
        scrape_tickets.start()
        print("🔍 Started scheduled ticket scraping (every 5 minutes)")

    print("🤖 Discord bot ready with automated ticket monitoring!")

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
    if await unwilling_to_speak(ctx):
        return

    msg = random_seat()
    await ctx.send(msg)

@bot.hybrid_command(name="paulback", description="抽保背")
async def back(ctx):
    if await unwilling_to_speak(ctx):
        return

    msg = paulback()
    await ctx.send(msg)

# Ticket Management Commands (Admin Only)
async def is_admin(ctx):
    """Check if user has administrator permissions in the guild"""
    # Commands only work in guilds, not in DMs
    if ctx.guild is None:
        return False

    # Check Discord administrator permission
    return ctx.author.guild_permissions.administrator

@bot.hybrid_command(name="post_tickets", description="手動投稿未發布的票券 (僅限管理員)")
async def cmd_post_tickets(ctx):
    """Manually post unposted tickets (Admin only)"""
    if not await is_admin(ctx):
        await ctx.send("❌ 此指令僅限管理員使用")
        return

    await ctx.send("🔄 開始投稿未發布的票券...")
    result = await post_unposted_tickets()

    if result["status"] == "success":
        if result["count"] == 0:
            await ctx.send("📊 目前沒有未投稿的票券")
        else:
            await ctx.send(f"✅ 成功投稿了 {result['count']} 張票券！")
    else:
        await ctx.send(f"❌ 錯誤: {result['message']}")

@bot.hybrid_command(name="ticket_status", description="查看未發布票券數量 (僅限管理員)")
async def cmd_ticket_status(ctx):
    """Check current unposted ticket count (Admin only)"""
    if not await is_admin(ctx):
        await ctx.send("❌ 此指令僅限管理員使用")
        return

    try:
        db = TicketDatabase()
        unposted_tickets = db.get_unposted_tickets('active')
        count = len(unposted_tickets)

        if count == 0:
            await ctx.send("📊 目前沒有未投稿的票券")
        else:
            await ctx.send(f"📊 目前有 {count} 張未投稿的票券")
    except Exception as e:
        await ctx.send(f"❌ 錯誤: {str(e)}")

@bot.hybrid_command(name="scrape_now", description="立即執行票券爬取 (僅限管理員)")
async def cmd_scrape_now(ctx):
    """Manually trigger immediate ticket scraping (Admin only)"""
    if not await is_admin(ctx):
        await ctx.send("❌ 此指令僅限管理員使用")
        return

    await ctx.send("🔍 開始爬取票券...")
    result = await manual_scrape()

    if result["status"] == "success":
        msg = f"✅ 爬取完成！\n"
        msg += f"新票券: {result['new_tickets']}\n"
        msg += f"更新票券: {result['updated_tickets']}\n"
        msg += f"刪除票券: {result['deleted_tickets']}\n"
        msg += f"價格變動: {result['price_changes']}"
        await ctx.send(msg)
    else:
        await ctx.send(f"❌ 錯誤: {result['message']}")

@bot.hybrid_command(name="admin_status", description="檢查管理員權限狀態")
async def cmd_admin_status(ctx):
    """Check admin permission status"""
    is_user_admin = await is_admin(ctx)

    if is_user_admin:
        msg = "✅ 您擁有票券管理權限\n\n"
        msg += "📋 **可用的票券指令:**\n"
        msg += "• `/post_tickets` - 手動投稿未發布的票券\n"
        msg += "• `/ticket_status` - 查看未發布票券數量\n"
        msg += "• `/scrape_now` - 立即執行票券爬取\n"
        msg += "• `/admin_status` - 檢查管理員權限狀態"
    else:
        if ctx.guild is None:
            msg = "❌ 票券管理指令不能在私訊中使用\n\n"
            msg += "🔒 請在伺服器中使用這些指令"
        else:
            msg = "❌ 您沒有票券管理權限\n\n"
            msg += "🔒 **權限說明:**\n"
            msg += "票券相關指令僅限擁有伺服器管理員權限的用戶使用"

    await ctx.send(msg)

if __name__ == "__main__":
    # Start Discord bot
    bot.run(TOKEN)
