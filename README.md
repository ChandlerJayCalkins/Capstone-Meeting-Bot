# Capstone-Meeting-Bot
Code for a Discord bot that keeps track of Senior Engineering Capstone Design meetings, agenda and meeting minutes duty, and birthdays too lol.
Built for engineering students at the University of Idaho.
Brief instructions for how to set up and run your own bot with this code are below.
Works with python 3.11.

# Required 3rd Party Libraries

## discord.py

### Windows

```py -3 -m pip install -U discord.py```

or, for voice support as well if you want (not required for this bot),

```py -3 -m pip install -u discord.py[voice]```

### Linux

```python3 -m pip install -U discord.py```

or, for voice support as well if you want (not required for this bot),

```python3 -m pip install -U discord.py[voice]```

## zoneinfo

```pip install tzdata```

# Discord Bot Token

Copy your discord bot's token and paste into a file called "`token.txt`" in the root directory of this repository (same folder / location as the code).
Make sure the file has nothing else in it except the token.
To create your own discord bot and get it's token, go to [the Discord Developer Portal](https://discord.com/developers/applications).

# Contact Info

Just like above, create a file called "`contact_info.txt`" in the root directory of this repository, and put a string that will display your contact info in it on the first line.
The bot will display this string to users so if they are having ay problems with it, they can contact you.
This is optional, the bot will still run without this file or if it's empty.

# Required Server Permissions for the Bot
- [x] Send Messages
- [x] Send Messages in Threads
- [x] Read Message History
- [x] Mention Everyone
- [x] Add Reactions
