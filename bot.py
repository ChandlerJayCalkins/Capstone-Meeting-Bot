# required permissions for the bot:
#	Send Messages
#	Send Messages in Threads
#	Embed Links
#	Attach Files
#	Read Message History
#	Add Reactions

import discord
import os
from datetime import datetime

# discord bot permissions
perms = discord.Intents.default()
perms.message_content = True

# sets up the bot client
client = discord.Client(intents = perms)

# gets the secret bot token by reading it from a local txt file
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
	desktop_prefix = f"<@!{client.user.id}>"
	mobile_prefix = f"<@{client.user.id}>"

	print("Bot is running")
	print(desktop_prefix)
	print(mobile_prefix)

async def help_command(message):
	help_reply = 'Usage:\n'
	help_reply += f'{desktop_prefix} [command] [argument argument argument...]'
	await message.reply(help_reply)

# returns true if a message is a command, false if it isn't
async def is_command(message) -> bool:
	# if the message is not a DM, not from the bot itself (prevents recursion), and starts with a command prefix
	if message.guild and message.author.id != client.user.id and message.content.startswith(desktop_prefix) or message.content.startswith(mobile_prefix):
		channel_perms = message.channel.permissions_for(message.guild.me)
		# if the bot has permission to send messages in the channel of the message
		if channel_perms.send_messages:
			# if the message has an actual command (has more than just the prefix token)
			if len(message.content.split()) > 1:
				return True
			# if the message is just @ing the bot with no command
			else:
				# reply with the help message and return false
				await help_command(message)
				return False

	return False

# handles commands
@client.event
async def on_message(message):
	print(message.content)
	# if the message is not a DM and the message is not from the bot (to prevent recursion)
	if await is_command(message):
		command = message.content.split()
		if command[1].lower() == 'help':
			await help_command(message)

client.run(token)