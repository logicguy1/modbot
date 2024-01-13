import discord
from discord import ui
import traceback
import time
import re
import pytz

from datetime import datetime, timedelta

from modules.embed import Embed


def convert_to_minutes(time_string):
    """Thx chatGPT"""
    pattern = re.compile(r'(\d+)([dhwmy])')
    conversion_factors = {'d': 1440, 'h': 60, 'm': 1, 'w': 10080, 'y': 525600}
    matches = pattern.findall(time_string)
    total_minutes = 0
    for value, unit in matches:
        total_minutes += int(value) * conversion_factors[unit]

    return total_minutes

def minutes_to_timedelta(minutes):
    """Thx chatGPT"""
    current_time = datetime.now(pytz.utc)
    delta = timedelta(minutes=minutes)
    future_time = current_time + delta
    return future_time


class TimeoutModal(ui.Modal, title='Apply Timeout'):
    timespan = ui.TextInput(label='Time', required=True, placeholder="Time formatted string 1m2h")

    def __init__(self, member_id):
        super().__init__()
        self.member_id = int(member_id)

    async def on_submit(self, interaction: discord.Interaction):
        print(self.timespan, convert_to_minutes(str(self.timespan)))
        member = interaction.guild.get_member(self.member_id)
        print(self.member_id)

        ends = minutes_to_timedelta(convert_to_minutes(str(self.timespan)))

        embed = Embed(title=f"Timeout Applied ({self.timespan})")
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Timestamp", value=f"<t:{int(time.time())}:R>", inline=True)
        embed.add_field(name="Duration", value=f"Until <t:{int(ends.timestamp())}:f> ends <t:{int(ends.timestamp())}:R>", inline=True)

        embed.set_color("red")

        try:
            await member.timeout(ends)
        except:
            embed = Embed(title="Timeout Failed", description="Management is not able to timeout this user")
            embed.set_color("red")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

            try:
                await member.send(embed=embed)
            except:
                await interaction.channel.send("```The user has DMS disabled, i am unable to contact.```")


class BanView(ui.View):
    def __init__(self, member_id):
        super().__init__(timeout = None)
        self.member_id = int(member_id)

    @discord.ui.button(label = "Yes", custom_id = "yesban", style = discord.ButtonStyle.danger)
    async def test(self, interaction: discord.Interaction, button: discord.Button):
        member = interaction.guild.get_member(self.member_id)

        embed = Embed(title=f"Ban Applied")
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Timestamp", value=f"<t:{int(time.time())}:R>", inline=True)

        embed.set_color("red")

        try:
            await member.send(embed=embed)
        except:
            await interaction.channel.send("```The user has DMS disabled, i am unable to contact.```")

        try:
            await member.ban()
        except:
            embed = Embed(title="Ban Failed", description="Management is not able to ban this user")
            embed.set_color("red")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

        await interaction.message.delete()

    @discord.ui.button(label = "No", custom_id = "noban", style = discord.ButtonStyle.gray)
    async def test2(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.message.delete()
        await interaction.response.send_message("Okidoki i wont ban em them")


class KickView(ui.View):
    def __init__(self, member_id):
        super().__init__(timeout = None)
        self.member_id = int(member_id)

    @discord.ui.button(label = "Yes", custom_id = "yesban", style = discord.ButtonStyle.danger)
    async def test(self, interaction: discord.Interaction, button: discord.Button):
        member = interaction.guild.get_member(self.member_id)

        embed = Embed(title=f"Kick Applied")
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Timestamp", value=f"<t:{int(time.time())}:R>", inline=True)

        embed.set_color("red")

        try:
            await member.send(embed=embed)
        except:
            await interaction.channel.send("```The user has DMS disabled, i am unable to contact.```")

        try:
            await member.ban()
        except:
            embed = Embed(title="Kick Failed", description="Management is not able to kick this user")
            embed.set_color("red")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

        await interaction.message.delete()

    @discord.ui.button(label = "No", custom_id = "noban", style = discord.ButtonStyle.gray)
    async def test2(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.message.delete()
        await interaction.response.send_message("Okidoki i wont kick em them")
