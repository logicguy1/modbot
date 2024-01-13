import discord
from discord import ui
import traceback
import time

from modules.embed import Embed

class OpenReportView(ui.View):
    def __init__(self):
        super().__init__(timeout = None)

        btn = ui.Button(label = "Open New Report", custom_id = "report", style = discord.ButtonStyle.danger)
        self.add_item(btn)


class ReportModal(ui.Modal, title='Report Member'):
    userid = ui.TextInput(label='User ID', required=False, placeholder="936357105760370729")
    content = ui.TextInput(label='Situation', style=discord.TextStyle.paragraph, required=False, placeholder="Will be shared with the reportee")

    def __init__(self):
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(1195412944440262698)
        member = interaction.guild.get_member(int(str(self.userid)))

        embed = Embed(title=f"Report - {member} ({member.id})")
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Timestamp", value=f"<t:{int(time.time())}:R>", inline=True)
        embed.add_field(name="Reason", value=f"```{self.content} ```", inline=True)

        embed.set_color("red")

        thread, msg = await channel.create_thread(
            name=f"{self.userid} - {member} - Report",
            embed=embed,
            applied_tags=[channel.available_tags[0]],
            view=ReportView(channel.id, member.id)
        )

        await msg.pin()

        try:
            embed.description = "A report has been opened on your account, if you want to say something to the mod team you can send a message in this thread."
            await member.send(embed = embed)
        except:
            await thread.send("```The user has DMS disabled, i am unable to contact.```")

        await interaction.response.send_message(f"Thank you for reporting, you can find any information regarding your report in {thread.mention}", ephemeral=True)


class ReportView(ui.View):
    def __init__(self, channel_id, user_id):
        super().__init__(timeout = None)

        btn = ui.Button(label = "Ban", custom_id = f"ban_{channel_id}_{user_id}", style = discord.ButtonStyle.grey)
        self.add_item(btn)

        btn = ui.Button(label = "Kick", custom_id = f"kick_{channel_id}_{user_id}", style = discord.ButtonStyle.grey)
        self.add_item(btn)

        btn = ui.Button(label = "Timeout", custom_id = f"mute_{channel_id}_{user_id}", style = discord.ButtonStyle.grey)
        self.add_item(btn)

