import discord 
from discord import app_commands
from discord.ext import commands
from discord import ui
import re
import time
import asyncio
import traceback
import sys
import uuid

from modules.embed import Embed

from ui.report import OpenReportView, ReportModal
from ui.action import TimeoutModal, BanView, KickView
from ui.error import OpenErrorView

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

GUILD_ID = 1178990094301007942

@tree.command(name = "showreport", description = "Show the HR Contact Form interface", guild=discord.Object(id=GUILD_ID)) 
async def create_table(ctx):
    print(ctx.user)
    print(ctx.user.id)
    if ctx.user.id not in [936357105760370729, 192083491217866752]: # Me :)
        await ctx.response.send_message("You don't have proper permissions to run this command, please consult the Security Team if you believe this is a mistake.", ephemeral=True)
        return
    embed = Embed(title = "Disciplinary Report Form", description = f"Utilize this interface to initiate a Disciplinary Report Form with a User.")
    await ctx.response.send_message("Did that for ya :)", ephemeral=True)
    await ctx.channel.send(embed = embed, view=OpenReportView())

@tree.command(name = "send", description = "Send a message to a reported user", guild=discord.Object(id=GUILD_ID))
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
    print(message)
    if not message.author.bot:
        print("Not bot")
        if message.content == "t!sync" and message.author.id == 936357105760370729: # Me :)
            await tree.sync()
            await message.channel.send("Command tree synced")

        if isinstance(message.channel, discord.channel.DMChannel):
            print("In dm")
            channel = await client.fetch_channel(1195412944440262698)
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
                        await i.send(
                            f"User sent an attachment `{a.filename}`\n{a.url}"
                        )

                    await message.add_reaction("✅")
                    found = True


@client.event
async def on_ready():
    print("Syncing..")
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("Synced!")


client.run("")

