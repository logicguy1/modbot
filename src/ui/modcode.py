import discord
from discord import ui
import traceback
import time

class ModCodeView(ui.View):
    def __init__(self, text):
        super().__init__(timeout = None)
        self.text = text

    @discord.ui.button(label = "View Mods", style = discord.ButtonStyle.primary)
    async def test(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_message(self.text, ephemeral=True)
