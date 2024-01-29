import discord
import requests
import io
import base64
import yaml
import datetime
from zipfile import ZipFile

from modules.embed import Embed
from modules.SQLiteMGR import SQLiteManager
from ui.modcode import ModCodeView

async def respond_to_code(msg, code, logging):
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
            modcount = len([i for i in data["mods"] if i['enabled']])

            db = SQLiteManager("database.db", logging)
            db.connect()

            mods = []
            for mod in data['mods']:
                name = "-".join(mod['name'].split('-')[1:])
                version = f"{mod['version']['major']}.{mod['version']['minor']}.{mod['version']['patch']}"
                if mod['enabled']:
                    mods.append(f"> `{name} - {version}`")

                    item = db.fetch_all(
                        "SELECT id FROM mod_entries WHERE modcode = ? AND mod = ?",
                        (code, mod['name'],)
                    )
                    if not item:
                        db.execute_query(
                            "INSERT INTO mod_entries (modcode, mod, timestamp) VALUES (?,?,?)", 
                            (code, mod['name'], datetime.datetime.now().strftime('%Y-%m-%d'),)
                        )
                else:
                    mods.append(f"> ~~`{name} - {version}`~~")

            db.close_connection()

            mod_array_display = "\n".join(mods)
            embed = Embed(title=f"ModCode - {name}", description=f"{msg.author.mention} posted a modcode with `{modcount} mods`.\n> **`{code}`**\n To browse the mods, use the button below.")
            await msg.reply(embed=embed, view=ModCodeView(text=mod_array_display))

    except requests.exceptions.RequestException as e:
        print(f"Oops, there was a problem reading the code. Please try again.\n{e}")
