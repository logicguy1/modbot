import discord
from discord import ui
import traceback
import time

class OpenErrorView(ui.View):
    def __init__(self, error, uid):
        super().__init__(timeout = None)
        self.error = error 
        self.uid = uid

    @discord.ui.button(label = "Report issue", custom_id = "report", style = discord.ButtonStyle.danger)
    async def test(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(ErrorModal(error=self.error, uid=self.uid))

class ErrorModal(ui.Modal, title='Report error'):
    email = ui.TextInput(label='Email', required=False, placeholder="bob@example.com, if we can contact you for more intel")
    content = ui.TextInput(label='Situation', style=discord.TextStyle.paragraph, required=False, placeholder="What happened for this error to occur?")

    def __init__(self, error, uid):
        super().__init__()

        self.error = error 
        self.uid = uid

        errorref = ui.TextInput(label='Referance', required=False, default=str(self.uid))
        self.add_item(errorref)

    async def on_submit(self, interaction: discord.Interaction):
        traceback_str = ''.join(traceback.format_exception(type(self.error), self.error, self.error.__traceback__))

        await interaction.response.send_message("Thank you for reporting the issue", ephemeral=True)

