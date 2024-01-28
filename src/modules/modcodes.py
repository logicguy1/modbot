import discord
import requests
import io
import base64
import yaml
from zipfile import ZipFile

from modules.embed import Embed
from ui.modcode import ModCodeView

async def respond_to_code(msg, code):
    url = "https://thunderstore.io/api/experimental/legacyprofile/get/" + code
    try:
        response = requests.get(url)
        response.raise_for_status()
        value = response.text

        if not value.startswith("#r2modman"):
            print("The code provided isn't a valid profile. Please re-export your code.")
            return

        encoded_data = value[9:].strip()
        decoded_data = base64.b64decode(encoded_data)

        with ZipFile(io.BytesIO(decoded_data)) as zip_file:
            export_r2x_data = zip_file.read("export.r2x")
            data = yaml.safe_load(export_r2x_data)

            name = data["profileName"]
            modcount = len([i for i in data["mods"] if mod['enabled'])

            mods = []
            for mod in data['mods']:
                name = "-".join(mod['name'].split('-')[1:])
                version = f"{mod['version']['major']}.{mod['version']['minor']}.{mod['version']['patch']}"
                if mod['enabled']:
                    mods.append(f"> `{name}` - `{version}`")
                else:
                    mods.append(f"> ~~`{name}`~~ - ~~`{version}`~~")

            mod_array_display = "\n".join(mods)
            embed = Embed(title=f"ModCode - {name}", description=f"{msg.author.mention} posted a modcode with `{modcount} mods`.\n`{code}`\n To browse the mods, use the button below.")
            await msg.reply(embed=embed, view=ModCodeView(text=mod_array_display))

    except requests.exceptions.RequestException as e:
        print(f"Oops, there was a problem reading the code. Please try again.\n{e}")
