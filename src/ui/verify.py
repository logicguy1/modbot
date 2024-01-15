import discord
from discord import ui
import traceback
import time
import requests

from config import Config
from modules.embed import Embed
from modules.SQLiteMGR import SQLiteManager


class OpenVerifyView(ui.View):
    def __init__(self):
        super().__init__(timeout = None)

        btn = ui.Button(label = "Verify my account", custom_id = "verify", style = discord.ButtonStyle.primary)
        self.add_item(btn)


async def verify_member(interaction):
    db = SQLiteManager("database.db")
    db.connect()

    log = interaction.guild.get_channel(Config.VERIFY_LOG)

    item = db.fetch_all(
        "SELECT id, user_id, timestamp FROM verify_attempts WHERE user_id = ?",
        (interaction.user.id,)
    )

    if len(item) != 0:
        item = item[0]
        t1 = float(item[2])
        tdiff = time.time() - t1

        if tdiff < Config.VERIFY_COOLDOWN:
            embed = Embed(description=f"Your next verification attempt is <t:{int(time.time() + (Config.VERIFY_COOLDOWN-tdiff))}:R>.")
            await interaction.response.send_message(embed=embed, delete_after=Config.VERIFY_COOLDOWN-tdiff, ephemeral=True)
            db.close_connection()
            return

        db.execute_query("UPDATE verify_attempts SET timestamp = ? WHERE user_id = ?", (str(time.time()), interaction.user.id))

    else:
        db.execute_query("INSERT INTO verify_attempts (user_id, timestamp) VALUES (?,?)", (interaction.user.id, str(time.time())))


    # Check account age (days)
    age = (time.time() - interaction.user.created_at.timestamp()) / 60 / 60 / 24
    if age < Config.ACCOUNT_MIN_AGE:
        embed = Embed(title="Too young", description=f"User {interaction.user.mention} attempted verification but account too young, account age: `{round(age,2)} day{'s' if age != 1 else ''}`.")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await log.send(embed=embed)

        embed = Embed(description=f"Your account is unable to be verified at this moment, it must be {Config.ACCOUNT_MIN_AGE} days or older.\nErrorref: `0xAFB4F3D163`.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        db.close_connection()
        return

    # Get connected accounts
    res = requests.get(
        f"https://discord.com/api/v9/users/{interaction.user.id}/profile?with_mutual_guilds=true&with_mutual_friends_count=false&guild_id={Config.GUILD_ID}",
        headers={"authorization": Config.USER_TOKEN}
    )

    data = res.json()
    connected = data.get("connected_accounts")

    # Check accounts connected
    if len(connected) < Config.ACCOUNT_MIN_CONNECT:
        embed = Embed(title="Not enough connections", description=f"User {interaction.user.mention} attempted verification but account has too little connections, connections: `{Config.ACCOUNT_MIN_CONNECT} account{'s' if Config.ACCOUNT_MIN_CONNECT !=1 else ''}`.")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await log.send(embed=embed)

        embed = Embed(description=f"Your account is unable to be verified at this moment, it must have at least {Config.ACCOUNT_MIN_CONNECT} external account{'s' if Config.ACCOUNT_MIN_CONNECT !=1 else ''} connected to it.\nErrorref: `0x11B5FE8A76`.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        db.close_connection()
        return

    # Check duplicate connections
    for c in connected:
        if c.get("verified"):
            item = db.fetch_all(
                "SELECT id, user_name, user_id, account_type, account_name, account_id FROM accounts WHERE account_id = ?",
                (c.get("id"),)
            )
            if len(item) != 0:
                embed = Embed(title="Already verifed", description=f"User {interaction.user.mention} attempted verification but one of their connected accounts was already verified by someone else.")
                embed.add_field(name="Account", value=f"<@{item[0][2]}> *[{item[0][3]}]* `{item[0][4]}` *(ID: {item[0][5]})*")
                embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
                await log.send(embed=embed)

                embed = Embed(description=f"It was not posible to verify your account, please contact a member of the Security Team if you belive this to be a mistake.\nErrorref: `0x493A488A74`.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                db.close_connection()
                return

    # Save listed connections
    for c in connected:
        if c.get("verified"):
            db.execute_query(
                "INSERT INTO accounts (user_name, user_id, account_type, account_name, account_id) VALUES (?,?,?,?,?)", 
                (
                    str(interaction.user),
                    interaction.user.id,
                    c.get("type"),
                    c.get("name"),
                    c.get("id")
                )
            )
    
    db.close_connection()

    role = interaction.guild.get_role(Config.VERIFY_ROLE)
    await interaction.user.add_roles(role)
    
    embed = Embed(description=f"Your account has been verified.")
    await interaction.response.send_message(embed=embed, ephemeral=True)
