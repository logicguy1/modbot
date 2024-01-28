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
        if len(self.text) >= 1900:
            out = ""
            carry = ""
            for i in self.text.split("\n"):
                if len(out) < 1900:
                    out += i + "\n"
                else:
                    carry += i + "\n"

            out += "`Max message length reached, use the button below to view the next set of mods`"
            await interaction.response.send_message(out, ephemeral=True, view=ModCodeView(text=carry))

        else:
            await interaction.response.send_message(self.text, ephemeral=True)
