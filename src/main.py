import discord 
from discord import app_commands
from discord.ext import commands
from discord import ui
import requests
import io
import re
import time
import asyncio
import traceback
import sys
import uuid
import base64
import yaml

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
CREATE TABLE IF NOT EXISTS "verify_attempts" (
	"id"	INTEGER,
	"user_id"	TEXT,
	"timestamp"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
)
""")
db.close_connection()

@tree.command(name = "showreport", description = "Show the HR Contact Form interface", guild=discord.Object(id=Config.GUILD_ID)) 
async def create_report(ctx):
    if ctx.user.id not in Config.ADMIN_IDS: # Me :)
        await ctx.response.send_message("You don't have proper permissions to run this command, please consult the Security Team if you believe this is a mistake.", ephemeral=True)
        return
    embed = Embed(title = "Disciplinary Report Form", description = f"Utilize this interface to initiate a Disciplinary Report Form with a User.")
    await ctx.response.send_message("Did that for ya :)", ephemeral=True)
    await ctx.channel.send(embed = embed, view=OpenReportView())


@tree.command(name = "showverify", description = "Show the HR Verification interface", guild=discord.Object(id=Config.GUILD_ID)) 
async def create_verify(ctx):
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


@tree.command(name = "send", description = "Send a message to a reported user", guild=discord.Object(id=Config.GUILD_ID))
async def send(ctx, message: str):
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
    if interaction.data.get("component_type") == 2 and interaction.data.get("custom_id") == "verify":
        print("Verifying")
        await verify_member(interaction, logging)


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
            await respond_to_code(message, found_uuids[0])

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
    logging.info("Syncing..")
    await tree.sync(guild=discord.Object(id=Config.GUILD_ID))
    logging.info("Synced!")


client.run(Config.BOT_TOKEN, log_handler=None)

