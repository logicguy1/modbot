# Modbot

An advanced moderation bot for discord server using slash commands and intercations API.

The bot allows moderators to open tickets, track issues, open up a two way modmail system while being very secure as you do not need your moderators to have ban or kick permissions, effecitvely making a server nuke less viable.

To set it up you will need to fill out the config file located in `src/config.py`, this file should include a user and bot token, the user token is used to validate new users with the verificaion system.

```py
# src/config.py

class Config:
    # Tokens
    BOT_TOKEN = ""
    USER_TOKEN = ""
    GUILD_ID = 1189379857327591474
    ADMIN_IDS = [936357105760370729, 192083491217866752]

    # Report system
    FORUM_ID = 1195412944440262698

    # Verification
    VERIFY_LOG = 1196067607405662298
    ACCOUNT_MIN_AGE = 7
    ACCOUNT_MIN_CONNECT = 1
    VERIFY_COOLDOWN = 120
```

A database will automaitcally be created using the following schema

```py
db.execute_query("""
CREATE TABLE IF NOT EXISTS "accounts" (
	"id"	INTEGER,
	"user_name"	TEXT,
	"user_id"	TEXT,
	"account_type"	TEXT,
	"account_name"	TEXT,
	"account_id"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
)
""")
db.execute_query("""
CREATE TABLE IF NOT EXISTS "verify_attempts" (
	"id"	INTEGER,
	"user_id"	TEXT,
	"timestamp"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
)
""")
```

