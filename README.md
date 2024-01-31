# Modbot

An advanced moderation bot for discord servers using the slash commands and intercations API. The bot is themed to a Lethal Company server, and includes misc utility commands for this purpose, if you're interested it is joinable [here](https://discord.gg/cosmiccollectors).

The bot allows moderators to open tickets, track issues, open up a two way modmail system while being very secure as you do not need your moderators to have ban or kick permissions, effecitvely making a server nuke less viable.

## Features
The bots main purpose is to aid in moderation wile providing a secure interface for moderators, as to avoid moderators getting compromised and minising damege to the server. The bot uses role based permissions instead of the default discord permissions, this provides a harder to script interface while still being convinient for moderators. 

### Moderation
- Handle verificaiton by checking the connected accounts to a new guild member, this is saved so another user trying to verify with the same credentials will be rejected.
- Handle tickets from server members, a server member can use a button to create a ticket that opens up between them and the server moderators.
- Internal report management and tracking, your staff team can open reports on a user to easily communicate, share proof and take actions on a guild members account.
- Linking tickets from the ticket system to reports in the report system, this intergration allows the staff team to escallate a ticket opened by a guild member into a report.

### Lethal company related
- Automatically detect mod codes and show specific information about the mods listed under the modcode from thunderstore.
- Show statistucs about most used mods 
- Show specific statistics about a single mod, as well as how often it has been used in the last 30 days.

### Todo
- Anti raid / server lockdown, this feature locks down your server by timeing out every user that sends a message, later the message will be sent to channel for deciding wheater or not to remove the member(s).


## Setup
To set it up you will need to fill out the config file located in `src/config.py`, this file should include a user and bot token, the user token is used to validate new users with the verificaion system.

```py
# src/config.py

class Config:
    # Tokens
    BOT_TOKEN = ""
    USER_TOKEN = ""
    GUILD_ID = 1189379857327591474
    ADMIN_IDS = [936357105760370729, 192083491217866752] # User IDs
    MOD_ROLE_ID = 1201828487821013003 # Role ID

    # Report system
    FORUM_ID = 1195101916506624050
    TICKET_CATEGORY_ID = 1189379857327591476
    ReportMentionCommandID = 1201818177148043274

    # Verification
    VERIFY_LOG = 1196067607405662298
    VERIFY_ROLE = 1196103134880211085
    ACCOUNT_MIN_AGE = 7
    ACCOUNT_MIN_CONNECT = 1
    VERIFY_COOLDOWN = 120

    # Statistics
    statisticsGetCommandID = 1201309172088721619
```

A database will automaitcally be created using sqlite3 


