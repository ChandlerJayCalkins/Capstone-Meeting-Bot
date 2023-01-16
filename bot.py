# required packages for this bot:
#	pip install discord

# required permissions for the bot:
#	Send Messages
#	Send Messages in Threads
#	Embed Links
#	Attach Files
#	Read Message History
#	Mention Everyone
#	Add Reactions

import discord
import os
from datetime import datetime
from pathlib import Path

# class for holding time data for weekly meetings
class WeeklyTime:
	# constructor
	def __init__(self, day, hour, minute):
		self.day = day
		self.hour = hour
		self.minute = minute
		# converts number 0 - 6 to string Monday - Sunday
		self.day_str = num_to_day(day)
		self.hour_str_24hr = str(hour)
		# converts converts 24 hour time number to 12 hour time number
		self.hour_str_12hr = str(WeeklyTime._to_12hr(hour))
		# stores am / pm for 12 hour time
		if hour < 12:
			self.ampm = 'am'
		else:
			self.ampm = 'pm'
		# makes sure minutes get an extra 0 in front of them if they're only 1 digit
		if minute < 10:
			self.minute_str = '0' + str(minute)
		else:
			self.minute_str = str(minute)
	
	# convert to string
	def __str__(self):
		return f'{self.day_str}s at {self.hour_str_24hr}:{self.minute_str} / {self.hour_str_12hr}:{self.minute_str} {self.ampm}'
	
	# less than < operator overload
	def __lt__(self, other) -> bool:
		# these first 2 if statements are to compensate for datetime making 0 be monday and 6 be sunday

		# if the self day is sunday but the other day is not
		if self.day == 6 and other.day != 6:
			return True
		# if the other day is sunday but the self day is not
		elif other.day == 6 and self.day != 6:
			return False
		# if the self day is sooner than the other day
		elif self.day < other.day:
			return True
		# if the self day is later than the other day
		elif self.day > other.day:
			return False
		# if the days are equal
		else:
			# if the self hour is sooner than the other hour
			if self.hour < other.hour:
				return True
			# if the self hour is later than the other hour
			elif self.hour > other.hour:
				return False
			# if the hours are equal
			else:
				return self.minute < other.minute
	
	# greater than > operator overload
	def __gt__(self, other) -> bool:
		# these first 2 if statements are to compensate for datetime making 0 be monday and 6 be sunday

		# if the self day is sunday but the other day is not
		if self.day == 6 and other.day != 6:
			return False
		# if the other day is sunday but the self day is not
		elif other.day == 6 and self.day != 6:
			return True
		# if the self day is later than the other day
		elif self.day > other.day:
			return True
		# if the self day is sooner than the other day
		elif self.day < other.day:
			return False
		# if the days are equal
		else:
			# if the self hour is later than the other hour
			if self.hour > other.hour:
				return True
			# if the self hour is sooner than the other hour
			elif self.hour < other.hour:
				return False
			# if the hours are equal
			else:
				return self.minute > other.minute
	
	# less than or equal to <= operator overload
	def __le__(self, other) -> bool:
		# these first 2 if statements are to compensate for datetime making 0 be monday and 6 be sunday

		# if the self day is sunday but the other day is not
		if self.day == 6 and other.day != 6:
			return True
		# if the other day is sunday but the self day is not
		elif other.day == 6 and self.day != 6:
			return False
		# if the self day is sooner than the other day
		elif self.day < other.day:
			return True
		# if the self day is later than the other day
		elif self.day > other.day:
			return False
		# if the days are equal
		else:
			# if the self hour is sooner than the other hour
			if self.hour < other.hour:
				return True
			# if the self hour is later than the other hour
			elif self.hour > other.hour:
				return False
			# if the hours are equal
			else:
				return self.minute <= other.minute
	
	# greater than or equal to >= operator overload
	def __ge__(self, other) -> bool:
		# these first 2 if statements are to compensate for datetime making 0 be monday and 6 be sunday

		# if the self day is sunday but the other day is not
		if self.day == 6 and other.day != 6:
			return False
		# if the other day is sunday but the self day is not
		elif other.day == 6 and self.day != 6:
			return True
		# if the self day is later than the other day
		elif self.day > other.day:
			return True
		# if the self day is sooner than the other day
		elif self.day < other.day:
			return False
		# if the days are equal
		else:
			# if the self hour is later than the other hour
			if self.hour > other.hour:
				return True
			# if the self hour is sooner than the other hour
			elif self.hour < other.hour:
				return False
			# if the hours are equal
			else:
				return self.minute >= other.minute
	
	# equal to == operator overload
	def __eq__ (self, other) -> bool:
		return self.day == other.day and self.hour == other.hour and self.minute == other.minute
	
	# not equal to != operator overload
	def __ne__ (self, other) -> bool:
		return self.day != other.day or self.hour != other.hour or self.minute != other.minute
	
	# takes a 24 hour number and returns a 12 hour number
	def _to_12hr(hour):
		if hour > 12:
			return hour - 12
		elif hour == 0:
			return 12
		else:
			return hour

# discord bot permissions
perms = discord.Intents.default()
perms.message_content = True

# sets up the bot client
client = discord.Client(intents = perms)

# gets the secret bot token by reading it from a local txt file
with open('token.txt', 'r') as file:
	bot_token = file.readline().strip()

# strings for the bot to detect commands
desktop_prefix = ""
mobile_prefix = ""

# used for keeping track of weekly meetings for a server
weekly_meetings = {}

# called as soon as the bot is fully online and operational
@client.event
async def on_ready():
	# strings that go at the start of commands to help the bot detect the command
	# it is currently "@{botname}"
	global desktop_prefix
	global mobile_prefix
	desktop_prefix = f"<@!{client.user.id}>"
	mobile_prefix = f"<@{client.user.id}>"

	# sets up and starts running the bot for each server it's in
	for server in client.guilds:
		startup_server(server)

	print("Bot is running")

# sets up all of the data for a server when it joins one or the bot starts running
def startup_server(server):
	server_folder_name = server.name[:128].replace(' ', '_')
	server_folder = f'servers/{server.id}-{server_folder_name}'
	meetings_file = f'{server_folder}/meetings.txt'
	# if the server folder doesn't exist, make one
	if not os.path.isdir('servers'):
		os.mkdir('servers')
	# if the folder for this server's data doesn't exist, make it
	if not os.path.isdir(server_folder):
		os.mkdir(server_folder)
	# if the server's meeting file doesn't exist, create one
	if not os.path.isfile(meetings_file):
		Path(meetings_file).touch()
	
	weekly_meetings[server] = []

# sets up the bot for a new server every time it joins one while running
@client.event
async def on_guild_join(server):
	startup_server(server)

# returns true if a message is a command, false if it isn't
async def is_command(message) -> bool:
	# if the message is not a DM, not from the bot itself (prevents recursion), and starts with a command prefix
	if message.guild and message.author.id != client.user.id and message.content.startswith(desktop_prefix) or message.content.startswith(mobile_prefix):
		# if the message has an actual command (has more than just the prefix token)
		if len(message.content.split()) > 1:
			return True
		# if the message is just @ing the bot with no command
		else:
			# reply with the help message and then return false
			await help_command(message)

	return False

# handles commands
@client.event
async def on_message(message):
	# if the message is not a DM and the message is not from the bot (to prevent recursion)
	if await is_command(message):
		# splits the command up into tokens by whitespace
		command = message.content.split()
		# turns the first token (command type) into all lowercase so it's easier and faster to check the command type
		command[1] = command[1].lower()
		# if it's the help command
		if command[1] == 'help':
			await help_command(message)
		# if it's the add meeting command
		elif command[1] == 'add':
			await add_command(message, command)
		# if it's the show meetings command
		elif command[1] == 'meetings':
			await meetings_command(message)

# handles the help command that displays a message about how to use commands
async def help_command(message):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to send messages in the channel of the message
	if channel_perms.send_messages:
		help_reply = 'Usage:\n'
		help_reply += f'{desktop_prefix} [command] [argument argument argument...]'
		await message.reply(help_reply)
	# if the bot doesn't have permission to send message in the channel, react to the message with an x
	else:
		await react_with_x(message)

# handles the add command that adds meetings to the server's meeting list
async def add_command(message, command):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to add reactions in this channel
	if channel_perms.add_reactions:
		# if the command follows the format "add weekly meeting on *day* at *time*"
		if command[2].lower() == 'weekly' and command[3].lower() == 'meeting' and command[4].lower() == 'on' and command[6].lower() == 'at':
			# get a number 0 to 6 of the day of the week
			day = day_to_num_plural(command[5])
			# if a valid day of the week was not inputted
			if day is None:
				await react_with_x(message)
				return
			
			hour = 0
			minute = 0
			# if the command has a "pm" or "am" after the time
			if len(command) > 8:
				hour, minute = str_to_time_12hr(command[7], command[8])
			else:
				hour, minute = str_to_time_24hr(command[7])
			# if a valid time was not inputted
			if hour is None:
				await react_with_x
				return
			
			# add the meeting time to the server's list of meeting times
			try:
				meeting_time = WeeklyTime(day, hour, minute)
				add_weekly_meeting(weekly_meetings[message.guild], meeting_time)
				await react_with_check(message)
			# if it fails, react with an x
			except:
				await react_with_x(message)
		# if the command follows the format "add meeting on *day* at *time"
		elif command[2].lower() == 'meeting' and command[3].lower() == 'on' and command[5].lower() == 'at':
			return
		# if the command follows the format "add birthday on *day*"
		elif command[2].lower() == 'birthday' and command[3].lower() == 'on':
			return

# handles the meetings command that shows all current meetings
async def meetings_command(message):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to send messages in the channel of the message
	if channel_perms.send_messages:
		reply = '```Weekly Meetings```\n'
		for i in range(len(weekly_meetings[message.guild])):
			reply += f'**{i+1}. {weekly_meetings[message.guild][i]}**\n\n'
		
		await message.reply(reply)
	# if the bot doesn't have permission to send message in the channel, react to the message with an x
	else:
		await react_with_x(message)

# makes the bot react to a message with a checkmark emoji if it's able to
async def react_with_check(message):
	channel_perms = message.channel.permissions_for(message.guild.me)
	if channel_perms.add_reactions and message is not None:
		await message.add_reaction("\u2705")

# makes the bot react to a message with an X emoji if it's able to
async def react_with_x(message):
	channel_perms = message.channel.permissions_for(message.guild.me)
	if channel_perms.add_reactions and message is not None:
		await message.add_reaction("\u274c")

# returns whether or not a string is a day of the week

def is_monday(token: str) -> bool:
	return token.lower() == 'm' or token.lower() == 'mon' or token.lower() == 'monday'

def is_tuesday(token: str) -> bool:
	return token.lower() == 'tu' or token.lower() == 'tue' or token.lower() == 'tues' or token.lower() == 'tuesday'

def is_wednesday(token: str) -> bool:
	return token.lower() == 'w' or token.lower() == 'wed' or token.lower() == 'wednesday'

def is_thursday(token: str) -> bool:
	return token.lower() == 'th' or token.lower() == 'thu' or token.lower() == 'thur' or token.lower() == 'thurs' or token.lower() == 'thursday'

def is_friday(token: str) -> bool:
	return token.lower() == 'f' or token.lower() == 'fri' or token.lower() == 'friday'

def is_saturday(token: str) -> bool:
	return token.lower() == 'sa' or token.lower() == 'sat' or token.lower() == 'saturday'

def is_sunday(token: str) -> bool:
	return token.lower() == 'su' or token.lower() == 'sun' or token.lower() == 'sunday'

# converts a day monday to sunday to a number 0 to 6
def day_to_num(day: str):
	if is_monday(day):
		return 0
	elif is_tuesday(day):
		return 1
	elif is_wednesday(day):
		return 2
	elif is_thursday(day):
		return 3
	elif is_friday(day):
		return 4
	elif is_saturday(day):
		return 5
	elif is_sunday(day):
		return 6
	else:
		return None

# converts a day monday to sunday (including plural days (mondays, wednesdays, etc.)) to a number 0 to 6
def day_to_num_plural(day: str):
	if is_monday(day) or day.lower() == 'mondays':
		return 0
	elif is_tuesday(day) or day.lower() == 'tuesdays':
		return 1
	elif is_wednesday(day) or day.lower() == 'wednesdays':
		return 2
	elif is_thursday(day) or day.lower() == 'thursdays':
		return 3
	elif is_friday(day) or day.lower() == 'fridays':
		return 4
	elif is_saturday(day) or day.lower() == 'saturdays':
		return 5
	elif is_sunday(day) or day.lower() == 'sundays':
		return 6
	else:
		return None

# converts a number 0 to 6 to a day of the week monday to sunday
def num_to_day(num: int):
	if num == 0:
		return 'Monday'
	elif num == 1:
		return 'Tuesday'
	elif num == 2:
		return 'Wednesday'
	elif num == 3:
		return 'Thursday'
	elif num == 4:
		return 'Friday'
	elif num == 5:
		return 'Saturday'
	elif num == 6:
		return 'Sunday'
	else:
		return None

# takes a string of the form hour:minute or just the hour with a second string of either "am" or "pm" and returns an hour in 24 hour time and a minute
def str_to_time_12hr(time: str, ampm: str):
	# splits the string into tokens by colons
	nums = time.split(':')
	# if the time is just the hour with no minute
	if len(nums) == 1:
		# if both the token is a number
		if nums[0].isnumeric():
			# turn the hour into a number and make the minute 0
			hour = int(nums[0])
			minute = 0
			# if the hour is between 1 and 12
			if hour > 0 and hour <= 12:
				# if the time is in pm and the hour is 12, add 12 to it to turn it into 24 hour time
				if ampm == 'pm' and hour != 12:
					hour += 12
				# if the time is in am and the hour is 12, turn the hour to 0 to turn it into 24 hour time
				elif ampm == 'am' and hour == 12:
					hour = 0
				
				return hour, minute
		
		# return none if the input was not valid
		return None, None
	# if the time is of the form hour:minute
	else:
		# if both the first and second tokens are numbers
		if nums[0].isnumeric() and nums[1].isnumeric():
			# turn the first and second tokens into numbers
			hour = int(nums[0])
			minute = int(nums[1])
			# if the hour is between 1 and 12 and the minute is between 0 and 59
			if hour > 0 and hour <= 12 and minute >= 0 and minute < 60:
				# if the time is in pm and the hour is 12, add 12 to it to turn it into 24 hour time
				if ampm == 'pm' and hour != 12:
					hour += 12
				# if the time is in am and the hour is 12, turn the hour to 0 to turn it into 24 hour time
				elif ampm == 'am' and hour == 12:
					hour = 0
				
				return hour, minute
		
		# return none if the input was not valid
		return None, None

# takes a string of the form hour:minute or just the hour with a second string of either "am" or "pm" and returns an hour in 24 hour time and a minute
def str_to_time_24hr(time: str):
	# splits the string into tokens by colons
	nums = time.split(':')
	# if the time is just the hour with no minute
	if len(nums) == 1:
		# if both the token is a number
		if nums[0].isnumeric():
			# turn the hour into a number and make the minute 0
			hour = int(nums[0])
			minute = 0
			# if the hour is between 0 and 23
			if hour >= 0 and hour < 24:
				return hour, minute
		
		# return none if the input was not valid
		return None, None
	# if the time is of the form hour:minute
	else:
		# if both the first and second tokens are numbers
		if nums[0].isnumeric() and nums[1].isnumeric():
			# turn the first and second tokens into numbers
			hour = int(nums[0])
			minute = int(nums[1])
			# if the hour is between 0 and 23 and the minute is between 0 and 59
			if hour >= 0 and hour < 24 and minute >= 0 and minute < 60:
				return hour, minute
		
		# return none if the input was not valid
		return None, None

# adds a weekly meeting time to a weekly meeting list in sorted order with a binary search
# returns true if the meeting was added to the list, false if that time is already in the list
def add_weekly_meeting(meetings: list, time: WeeklyTime) -> bool:
	# if the meeting list is empty, just add the meeting to the list
	if len(meetings) == 0:
		meetings.append(time)
	# if there's only 1 item in the list
	elif len(meetings) == 1:
		if time < meetings[0]:
			meetings.insert(0, time)
		elif time > meetings[0]:
			meetings.append(time)
		# if the time is a duplicate
		else:
			return False
	# if the list has at least 2 meetings, do a binary insert
	else:
		# start by checking entire list
		low = 0
		high = len(meetings) - 1
		# while there are more than 2 more list items to check
		while high - low > 1:
			# get mid point of remaining list to check
			mid = (high - low) // 2 + low
			# if the time is less than the mid point, remove the upper half of the remaining list to check
			if time < meetings[mid]:
				high = mid - 1
			# if the time is greater than the mid point, remove the lower half of the remaining list to check
			elif time > meetings[mid]:
				low = mid + 1
			# if the time is a duplicate
			else:
				return False
		
		# if the time is between the last 2 items
		if time > meetings[low] and time < meetings[high]:
			# insert the time between those 2 items
			meetings.insert(high, time)
		# if the time is less than the lower last item
		elif time < meetings[low]:
			# insert the time in front of that item
			meetings.insert(low, time)
		# if the time is greater than the higher last item
		elif time > meetings[high]:
			# insert the time after that item
			meetings.insert(high + 1, time)
		# if the time is equal to one of those times
		else:
			return False
	
	return True

client.run(bot_token)