import discord
import os
from datetime import datetime

perms = discord.Intents.default()
perms.message_content = True

client = discord.Client(intents = perms)

with open('token.txt', 'r') as file:
	token = file.readline().strip()

# strings for the bot to detect commands
desktop_prefix = ""
mobile_prefix = ""

# called as soon as the bot is fully online and operational
@client.event
async def on_ready():
	# strings that go at the start of commands to help the bot detect the command
	# it is currently "@{botname}"
	global desktop_prefix
	global mobile_prefix
	desktop_prefix = f"<@!{client.user.id}> "
	mobile_prefix = f"<@{client.user.id}> "

	print("Bot is running")

client.run(token)