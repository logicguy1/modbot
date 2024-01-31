import discord
from discord import ui
import traceback
import time
import datetime
import io

from config import Config
from modules.embed import Embed
from modules.SQLiteMGR import SQLiteManager


class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout = None)

        btn = ui.Button(label = "Open Ticket", custom_id = "ticketnew", style = discord.ButtonStyle.primary)
        self.add_item(btn)


async def create_ticket(ctx, logging):
    print("Creating ticket")
    channel = ctx.guild.get_channel(Config.TICKET_CHANNEL_ID)

    db = SQLiteManager("database.db", logging)
    db.connect()

    idx = db.fetch_all("SELECT id FROM tickets ORDER BY id DESC LIMIT 1;",)[0][0] + 1

    thread = await channel.create_thread(name=f"Ticket-{str(idx).zfill(4)}", type=discord.ChannelType.private_thread)

    db.execute_query(
        "INSERT INTO tickets (id, author_id, channel_id, timestamp, referance) VALUES (?,?,?,?,?)", 
        (
            idx, 
            ctx.user.id, 
            thread.id, 
            str(datetime.datetime.now()), 
            f"Ticket-{str(idx).zfill(4)}"
        )
    )

    db.close_connection()

    embed = Embed(title="Ticket Created", description="Your ticket has been opened and our HR team has been notified, please describe your issue in detail so your matters can be handeled switly.")

    embed.add_field(name="Author", value=f"{ctx.user.mention} *({str(ctx.user)})*", inline=True)
    embed.add_field(name="Timestamp", value=f"<t:{int(time.time())}:R>", inline=True)
    embed.add_field(name="Ticket referance", value=f"`Ticket-{str(idx).zfill(4)}`", inline=True)

    msg = await thread.send(f"<@&1201828487821013003>", embed=embed, view=TicketInterfaceView())
    await msg.pin()
    await thread.add_user(ctx.user)
    await ctx.response.send_message(f"Your ticket has been opened as <#{thread.id}>.", ephemeral=True)


class LinkView(ui.View):
    def __init__(self, options, logging):
        super().__init__(timeout = None)

        print(options)
        self.logging = logging

        select = ui.Select(
            min_values=1, 
            max_values=1, 
            placeholder="Choose a ticket", 
            options=[discord.SelectOption(label=i, value=i) for i in options]
        )
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, ctx: discord.Interaction):
        referance = ctx.data["values"][0]
        db = SQLiteManager("database.db", self.logging)
        db.connect()

        ticket = db.fetch_all("SELECT id, author_id, channel_id, timestamp, referance FROM tickets WHERE referance = ?;", (referance,))
        if not ticket:
            embed = Embed(title="Ticket referance", description=f"No ticket with the referance code **`{referance}`**, please try agein.")
            embed.set_color("red")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            db.close_connection()
            return

        if len(ticket) != 1:
            out = f"The following {len(ticket)} were found, please choose only one.\n\n"

            for i in ticket:
                out += f"> `{i[4]}`\n"

            out += f"\nUse </report mention:{Config.ReportMentionCommandID}> and the referance to mention the ticket."

            embed = Embed(title="Ticket referance", description=out)
            await ctx.response.send_message(embed=embed, ephemeral=True)
            db.close_connection()
            return

        db.execute_query("UPDATE tickets SET report_id = ? WHERE id = ?", (ctx.channel.id, ticket[0][0]))

        embed = Embed(title="Ticket Mention", description=f"{ctx.user.mention} referanced <#{ticket[0][2]}> <t:{int(time.time())}:R>.")
        embed.add_field(name="Opned by", value=f"<@{ticket[0][1]}>")
        embed.add_field(name="Timestamp", value=f"<t:{int(time.mktime(datetime.datetime.strptime(ticket[0][3], '%Y-%m-%d %H:%M:%S.%f').timetuple()))}:f>")
        embed.add_field(name="Ticket Referance", value=f"`{ticket[0][4]}`")
        await ctx.response.send_message(embed=embed)

        channel = ctx.guild.get_channel(Config.TICKET_CHANNEL_ID)
        thread = channel.get_thread(int(ticket[0][2]))

        embed = Embed(title="Ticket Mentioned", description=f"The ticket was mentioned in `{ctx.channel.name}` and has been linked as a referance.")
        embed.add_field(name="Mentioned by", value=f"{ctx.user.mention}")
        embed.add_field(name="Timestamp", value=f"<t:{int(time.time())}:R>")
        embed.add_field(name="Ticket Referance", value=f"`{ticket[0][4]}`")

        await thread.send(embed=embed)


async def link_ticket(ctx, logging):
    db = SQLiteManager("database.db", logging)
    db.connect()
    items = db.fetch_all("SELECT referance FROM tickets WHERE status = 'open' ORDER BY id DESC LIMIT 25")
    db.close_connection()

    await ctx.response.send_message("Please select a ticket to link", view=LinkView(options=[i[0] for i in items], logging=logging), ephemeral=True)


class TicketInterfaceView(ui.View):
    def __init__(self):
        super().__init__(timeout = None)

        btn = ui.Button(label = "Close Ticket", custom_id = "ticketclose", style = discord.ButtonStyle.danger)
        self.add_item(btn)

        btn = ui.Button(label = "Add member", custom_id = "ticketadd", style = discord.ButtonStyle.primary)
        self.add_item(btn)

        btn = ui.Button(label = "Remove member", custom_id = "ticketremove", style = discord.ButtonStyle.primary)
        self.add_item(btn)


def split_lines(text):
    """Thx ChatGPT"""
    lines = text.split("\n")
    split_lines = []
    for line in lines:
        if len(line) > 100:
            # Split line into chunks of 300 characters
            split_lines.extend([line[i:i+100] for i in range(0, len(line), 100)])
        else:
            split_lines.append(line)
    return split_lines


async def close_ticket(ctx, logging):
    channel = ctx.channel

    db = SQLiteManager("database.db", logging)
    db.connect()
    ticket = db.fetch_all("SELECT id, author_id, timestamp, referance, report_id FROM tickets WHERE channel_id = ?", (channel.id,))[0]

    messages = [message async for message in channel.history(limit=None, oldest_first=True)]
    print(messages)
    messagecount = len(messages)
    authors = {}
    for i in messages:
        if i.author not in authors:
            authors[i.author] = 0
        
        authors[i.author] += 1

    owner = ctx.guild.get_member(int(ticket[1]))
    out = "<Ticket-Info>\n"
    out += f"    Ticket Referance: {ticket[3]}\n"
    out += f"    Ticket Owner: {owner} ({owner.id})\n"
    out += f"    Ticket Opned: {datetime.datetime.strptime(ticket[2], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')}\n"
    out += f"    Ticket Closed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    out += "\n<User-Info>\n"
    numberlength = len(str(max(authors.values())))
    namelength = len(max([str(i) for i in authors.keys()], key=len))
    for user, msgcount in authors.items():
        out += f"    {msgcount:<{numberlength}} - {user} ({user.id})\n"

    out += "\n<Message-Content>\n"
    for i in messages:
        if i.embeds and i.author.bot:
            out += f"    {i.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {str(i.author):<{namelength}} : {i.embeds[0].title}\n"
            content = split_lines(i.embeds[0].description)
            for text in content:
                out += f"                          {' '*namelength}   {text}\n"
        else:
            content = split_lines(i.content)
            out += f"    {i.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {str(i.author):<{namelength}} : {content[0]}\n"
            for text in content[1:]:
                out += f"                          {' '*namelength}   {text}\n"

    buf = io.BytesIO()
    buf.write(out.encode('utf-8'))
    buf.seek(0)  # Reset the buffer position to the beginning

    embed = Embed(title="Ticket Closed", description="This ticket has been closed and will be archived shortly.")
    if ticket[4]:
        embed.description += f"\n\n> **This ticket was mentioned in**\n> <#{ticket[4]}>\n> A transcript has been uploaded to the report."

    await ctx.response.send_message(embed=embed)

    if ticket[4]:
        forum = ctx.guild.get_channel(Config.FORUM_ID)
        channel = forum.get_thread(int(ticket[4]))

        embed = Embed(title="Ticket Closed", description=f"{ctx.channel.mention} was previusly linked to this report and has now been marked as closed. A full transcript and a list of the embedded attachments can be found below.")
        embed.add_field(name="Closed", value=f"<t:{int(time.time())}:R>")
        embed.add_field(name="Ticket Referance", value=f"`{ticket[3]}`")

        await channel.send(embed=embed)
        await channel.send(file=discord.File(buf, filename="transcript-{ticket[3]}.txt"))

        for msg in messages:
            for i in msg.attachments:
                await channel.send(f"{msg.author}: `{i.filename}` ({i.url})")
    
    db.execute_query("UPDATE tickets SET status = ? WHERE id = ?", ("closed", ticket[0]))
    await ctx.channel.edit(archived=True, locked=True)

    db.close_connection()


class AddView(ui.View):
    def __init__(self, logging):
        super().__init__(timeout = None)

        self.logging = logging

        select = ui.UserSelect(
            min_values=1, 
            max_values=1, 
            placeholder="Choose a member", 
        )
            #type=discord.ComponentType.user_select
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, ctx: discord.Interaction):
        memberid = ctx.data["values"][0]
        channel = ctx.channel
        member = ctx.guild.get_member(int(memberid))

        await channel.add_user(member)
        embed = Embed(title="Member added", description=f"{ctx.user.mention} has added <@{memberid}> to the ticket.")
        await ctx.response.send_message(embed=embed)


class RemoveView(ui.View):
    def __init__(self, logging):
        super().__init__(timeout = None)

        self.logging = logging

        select = ui.UserSelect(
            min_values=1, 
            max_values=1, 
            placeholder="Choose a member", 
        )
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, ctx: discord.Interaction):
        memberid = ctx.data["values"][0]
        channel = ctx.channel
        member = ctx.guild.get_member(int(memberid))

        await channel.remove_user(member)
        embed = Embed(title="Member removed", description=f"{ctx.user.mention} has removed <@{memberid}> from the ticket.")
        await ctx.response.send_message(embed=embed)


async def add_user(ctx, logging):
    await ctx.response.send_message("Please select a user to add", view=AddView(logging=logging), ephemeral=True)

async def remove_user(ctx, logging):
    await ctx.response.send_message("Please select a user to remove", view=RemoveView(logging=logging), ephemeral=True)
