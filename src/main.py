import discord 
from discord import app_commands
from discord.ext import commands
from discord import ui
import requests
from bs4 import BeautifulSoup
import io
import re
import time
import asyncio
import traceback
import sys
import uuid
import base64
import math
import yaml
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["figure.figsize"] = (10,5)

import logging
logging.basicConfig(level=logging.INFO)

from config import Config
from modules.embed import Embed
from modules.SQLiteMGR import SQLiteManager
from modules.modcodes import respond_to_code

from ui.report import OpenReportView, ReportModal
from ui.action import TimeoutModal, BanView, KickView
from ui.error import OpenErrorView
from ui.verify import OpenVerifyView, verify_member
from ui.ticket import TicketView, create_ticket, link_ticket, close_ticket, add_user, remove_user

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

db = SQLiteManager("database.db", logging)
db.connect()
db.execute_query("""
CREATE TABLE IF NOT EXISTS "accounts" (
	"id"	INTEGER,
	"user_name"	TEXT,
	"user_id"	TEXT,
	"account_type"	TEXT,
	"account_name"	TEXT,
	"account_id"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
)
""")
db.execute_query("""
CREATE TABLE IF NOT EXISTS "mod_entries" (
	"id"	INTEGER,
	"modcode"	TEXT,
	"mod"	TEXT,
	"timestamp"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
)
""")
db.execute_query("""
CREATE TABLE IF NOT EXISTS "verify_attempts" (
	"id"	INTEGER,
	"user_id"	TEXT,
	"timestamp"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
)
""")

db.execute_query("""
CREATE TABLE IF NOT EXISTS "tickets" (
	"id"	INTEGER,
	"author_id"	TEXT,
	"channel_id"	TEXT,
	"timestamp"	TEXT,
	"referance"	TEXT,
	"report_id"	TEXT,
	"status"	TEXT DEFAULT 'open',
	PRIMARY KEY("id" AUTOINCREMENT)
)
""")

db.close_connection()

class SetupGroup(app_commands.Group):
    @tree.command(name = "internalreport", description = "Show the HR Contact Form interface", guild=discord.Object(id=Config.GUILD_ID)) 
    async def create_report(self, ctx):
        if ctx.user.id not in Config.ADMIN_IDS: # Me :)
            await ctx.response.send_message("You don't have proper permissions to run this command, please consult the Security Team if you believe this is a mistake.", ephemeral=True)
            return
        embed = Embed(title = "Disciplinary Report Form", description = f"Utilize this interface to initiate a Disciplinary Report Form with a User.")
        await ctx.response.send_message("Did that for ya :)", ephemeral=True)
        await ctx.channel.send(embed = embed, view=OpenReportView())

    @tree.command(name = "verify", description = "Show the internal HR Verification interface", guild=discord.Object(id=Config.GUILD_ID)) 
    async def create_verify(self, ctx):
        if ctx.user.id not in Config.ADMIN_IDS: # Me :)
            await ctx.response.send_message("You don't have proper permissions to run this command, please consult the Security Team if you believe this is a mistake.", ephemeral=True)
            return
        embed = Embed(title = "HR Verification Interface", description = f"""Management requires new employees at the company to verify themselves, this is to avoid spam accounts from entering the sever.

To be eligable to join the company you must comply with the following:
- Your account must be `{Config.ACCOUNT_MIN_AGE}` day{'s' if Config.ACCOUNT_MIN_AGE !=1 else ''} or older.
- You must have at least `{Config.ACCOUNT_MIN_CONNECT}` external account{'s' if Config.ACCOUNT_MIN_CONNECT !=1 else ''} connected to your profile.

**We will never refer you to an external site or ask you for any personal information**""")
        await ctx.response.send_message("Did that for ya :)", ephemeral=True)
        await ctx.channel.send(embed = embed, view=OpenVerifyView())

    @tree.command(name = "ticket", description = "Show the external HR Contact Form interface", guild=discord.Object(id=Config.GUILD_ID)) 
    async def create_ticket(self, ctx):
        if ctx.user.id not in Config.ADMIN_IDS: # Me :)
            await ctx.response.send_message("You don't have proper permissions to run this command, please consult the Security Team if you believe this is a mistake.", ephemeral=True)
            return
        embed = Embed(title = "Human Resources", description = f"For urgent matters requiring immediate attention, we encourage you to open support tickets here, enabling seamless communication with our dedicated team of moderators who are committed to resolving issues promptly and ensuring a positive experience..")
        await ctx.response.send_message("Did that for ya :)", ephemeral=True)
        await ctx.channel.send(embed = embed, view=TicketView())


class ReportGroup(app_commands.Group):
    @tree.command(name = "send", description = "Send a message to a reported user", guild=discord.Object(id=Config.GUILD_ID))
    async def send(self, ctx, message: str):
        member = ctx.guild.get_member(int(ctx.channel.name.split(" - ")[0]))
        if member is not None:
            embed = Embed(description=message)
            embed.set_author(
                name=str(ctx.user),
                icon_url=ctx.user.display_avatar.url,
            )
            embed.set_color("blue")

            await member.send(embed=embed)
            await ctx.response.send_message(embed=embed)
        else:
            embed = Embed(description="Unable to send message")
            embed.set_author(
                name=str(ctx.user.author),
                icon_url=ctx.user.display_avatar.url,
            )
            embed.set_color("blue")
            await ctx.response.send_message(embed=embed)


class StatisticsGroup(app_commands.Group):
    @app_commands.command(name = "leaderboard", description = "View the most used mods in the server")
    async def leaderboard(self, ctx, page: int = 1):
        db = SQLiteManager("database.db", logging)
        db.connect()

        pagecount = math.ceil(db.fetch_all(f"SELECT COUNT(*) AS row_count FROM (SELECT DISTINCT mod FROM mod_entries) AS distinct_mods;",)[0][0] / 10)
        if pagecount < page or page <= 0:
            db.close_connection()
            await ctx.response.send("Invalid page number", ephemeral=True)
            return

        mods = db.fetch_all(f"SELECT mod, count(mod) FROM mod_entries GROUP BY mod ORDER BY count(mod) DESC LIMIT 10 OFFSET {(page-1)*10}",)

        db.close_connection()

        out = "See what the most popular mods in Cosmic Collectors are\n\n"
        for idx, i in enumerate(mods):
            out += f"> *{idx+1 + (page-1)*10}.* `{i[0]}` - {i[1]} uses\n"

        out += f"\n*```Page {page}/{pagecount}```*"

        embed = Embed(title="Mod leaderboard", description=out)
        await ctx.response.send_message(embed=embed)

    @app_commands.command(name = "get", description = "View specific information about a single mod")
    async def get(self, ctx, mod: str):
        db = SQLiteManager("database.db", logging)
        db.connect()

        mods = db.fetch_all(f"SELECT DISTINCT mod FROM mod_entries WHERE mod LIKE ?;", ("%" + mod + "%", ))
        if len(mods) != 1:
            db.close_connection()

            out = f"The following {len(mods)} were found, please choose only one.\n\n"

            for i in mods:
                out += f"> `{i[0]}`\n"

            out += f"\nUse </statistics get:{Config.statisticsGetCommandID}> and the name of the mod to fetch the mod data."

            embed = Embed(title="Mod lookup", description=out)
            await ctx.response.send_message(embed=embed, ephemeral=True)

            return

        modname = mods[0][0]
        data = db.fetch_all("SELECT count(mod), timestamp FROM mod_entries WHERE mod=? GROUP BY timestamp ORDER BY timestamp;", (modname,))

        # Function to generate a list of the last 30 days
        def last_30_days():
            end_date = datetime.now()
            start_date = end_date - timedelta(days=29)
            return [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]

        existing_dates = set(date for count, date in data)

        last_30_days_list = last_30_days()

        result = []
        for date in last_30_days_list:
            if date in existing_dates:
                # Use the tuple data if the date exists
                result.append(next(item for item in data if item[1] == date))
            else:
                # Create a zero input if the date doesn't exist
                result.append((0, date))

        result = [(i[0], "-".join(i[1].split("-")[1:][::-1])) for i in result]

        plt.bar(
            x=[i[1] for i in result],
            height=[i[0] for i in result]
        )
        plt.xticks(rotation=-60)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)  # Reset the buffer position to the beginning

        total = sum([i[0] for i in result])

        out = f"`{modname}` has been used `{result[-1][0]}` time{'s' if result[-1][0] != 1 else ''} today, "
        out += f"and `{total}` time{'s' if total != 1 else ''} in the last 30 days."

        author = modname.split("-")[0]
        name = "-".join(modname.split("-")[1:])
        print(author, name)

        response = requests.get(f"https://thunderstore.io/c/lethal-company/p/{author}/{name}/")
        soup = BeautifulSoup(response.content, "html.parser")

        header = soup.find("div", class_="card-header")
        img = header.find("img", class_="align-self-center")["src"]

        body = soup.find("div", class_="card-body")
        table = list(body.find("table").children)
        downloads = table[3].text.split("\n")[2].strip()
        likes = table[5].text.split("\n")[2].strip()
        print(downloads, likes)

        embed = Embed(title=f"Statistics - {modname}", description=out)
        embed.set_thumbnail(url=img)

        embed.add_field(name="Downloads", value="`"+downloads+"` <:LethalPoint:1187900986300309566>", inline=True)
        embed.add_field(name="Likes", value="`"+likes+"` <:LethalUwU:1188231578674004030>", inline=True)

        await ctx.response.send_message(file=discord.File(buf, filename="card.png"), embed=embed)


@client.event
async def on_interaction(interaction):
    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id") == "report":
        await interaction.response.send_modal(ReportModal())

    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id").startswith("ban"):
        await interaction.response.send_message(
            "Are you sure you want to ban this member?",
            view=BanView(
                member_id=interaction.data.get("custom_id").split("_")[2], 
            )
        )

    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id").startswith("kick"):
        await interaction.response.send_message(
            "Are you sure you want to kick this member?",
            view=KickView(
                member_id=interaction.data.get("custom_id").split("_")[2], 
            )
        )

    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id").startswith("mute"):
        await interaction.response.send_modal(
            TimeoutModal(
                member_id=interaction.data.get("custom_id").split("_")[2]
            )
        )

    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id").startswith("link"):
        await link_ticket(interaction, logging)

    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id") == "verify":
        await verify_member(interaction, logging)

    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id") == "ticketnew":
        await create_ticket(interaction, logging)

    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id") == "ticketclose":
        await close_ticket(interaction, logging)

    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id") == "ticketadd":
        await add_user(interaction, logging)

    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id") == "ticketremove":
        await remove_user(interaction, logging)



@tree.error
async def on_app_command_error(
    interaction,
    error
):
    traceback_str = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    print(traceback_str)
    uid = uuid.uuid4()
    embed = Embed(title = "Exception in command", description = f"An unexpected error was encountered\n```py\n{error}```\n*Error referance: `{uid}`*")
    embed.set_color("red")
    try:
        await interaction.response.send_message(embed=embed, view=OpenErrorView(error=error, uid=uid), ephemeral=True)
    except discord.errors.InteractionResponded:
        await interaction.channel.send(interaction.user.mention, embed=embed, view=OpenErrorView(error=error, uid=uid))


@client.event
async def on_message(message):
    print(str(message.author), str(message.content))
    if not message.author.bot:
        # Sync command
        if message.content == "t!sync" and message.author.id in Config.ADMIN_IDS: # Me :)
            await tree.sync()
            await message.channel.send("Command tree synced")

        # Detect modcodes
        uuid_pattern = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
        found_uuids = uuid_pattern.findall(message.content)
        if found_uuids:
            await respond_to_code(message, found_uuids[0], logging)

        # Modmail system
        if isinstance(message.channel, discord.channel.DMChannel):
            channel = await client.fetch_channel(Config.FORUM_ID)
            found = False
            for i in channel.threads:
                if (
                    i.name.startswith(str(message.author.id))
                    and len(i.applied_tags) == 1
                ):
                    embed = Embed(description=message.content)
                    embed.set_author(
                        name=str(message.author),
                        icon_url=message.author.display_avatar.url,
                    )
                    embed.set_color("green")
                    await i.send(embed=embed)

                    for a in message.attachments:
                        await i.send(f"User sent an attachment `{a.filename}`\n{a.url}")

                    await message.add_reaction("✅")
                    found = True


@client.event
async def on_ready():
    statisticsgroup = StatisticsGroup(name="statistics", description="View statistics about the server", guild_ids=[Config.GUILD_ID,])
    tree.add_command(statisticsgroup)

    setupgroup = SetupGroup(name="setup", description="Basic setup commands for the bot", guild_ids=[Config.GUILD_ID,])
    tree.add_command(setupgroup)

    reportgroup = ReportGroup(name="report", description="Interaction comamnds for the report system", guild_ids=[Config.GUILD_ID,])
    tree.add_command(reportgroup)

    logging.info("Syncing..")
    await tree.sync(guild=discord.Object(id=Config.GUILD_ID))
    logging.info("Synced!")


client.run(Config.BOT_TOKEN, log_handler=None)

