# file extension meaings:
#	.lst - list files (contain lists of plaintext data separated by line breaks)
#	.cfg - configuration files (settings)

import discord
import sys
import os
import shutil
import datetime
from pathlib import Path

########################################################################################################################
#
# class definitions
#
########################################################################################################################

# class for storing bday dates and names
class BDay:
	def __init__(self, date: datetime.date, name: str):
		self.date = date
		self.name = name
	
	def __str__(self):
		# Linux version:
		# date_str = self.date.strftime('%b %-d')
		# Windows version:
		date_str = self.date.strftime('%b %#d')
		bday_str = f'{self.name}: {date_str}'
		return bday_str
	
	def __eq__(self, other) -> bool:
		return self.date == other.date and self.name == other.name


# class for storing a server's data (like agenda order list and meeting times)
class ServerData:
	def __init__(self, server):
		self.server = server
		self.meetings = []
		self.weekly_meetings = []
		self.agenda_order = []
		self.agenda_index = 0
		self.minutes_order = []
		self.minutes_index = 0
		self.next_meeting = None
		self.next_weekly_meeting = None
		# set the meeting / bday alert channel to the first channel that the bot has message sending permissions in
		self.alert_channel = self.find_first_message_channel()
		self.bdays = []
	
	# adds a meeting time to the meeting list in sorted order with a binary search
	# returns true if the meeting was added to the list, false if that time is already in the list
	def add_meeting(self, time: datetime.datetime) -> bool:
		# if the meeting list is empty, just add the meeting to the list
		if len(self.meetings) == 0:
			self.meetings.append(time)
		# if there's only 1 item in the list
		elif len(self.meetings) == 1:
			if time < self.meetings[0]:
				self.meetings.insert(0, time)
			elif time > self.meetings[0]:
				self.meetings.append(time)
			# if the time is a duplicate
			else:
				return False
		# if the list has at least 2 meetings, do a binary insert
		else:
			# start by checking entire list
			low = 0
			high = len(self.meetings) - 1
			# while there are more than 2 more list items to check
			while high - low > 1:
				# get mid point of remaining list to check
				mid = (high - low) // 2 + low
				# if the time is less than the mid point, remove the upper half of the remaining list to check
				if time < self.meetings[mid]:
					high = mid - 1
				# if the time is greater than the mid point, remove the lower half of the remaining list to check
				elif time > self.meetings[mid]:
					low = mid + 1
				# if the time is a duplicate
				else:
					return False
			
			# if the time is between the last 2 items
			if time > self.meetings[low] and time < self.meetings[high]:
				# insert the time between those 2 items
				self.meetings.insert(high, time)
			# if the time is less than the lower last item
			elif time < self.meetings[low]:
				# insert the time in front of that item
				self.meetings.insert(low, time)
			# if the time is greater than the higher last item
			elif time > self.meetings[high]:
				# insert the time after that item
				self.meetings.insert(high + 1, time)
			# if the time is equal to one of those times
			else:
				return False
		
		return True
	
	# adds a weekly meeting time to a weekly meeting list in sorted order with a binary search
	# returns true if the meeting was added to the list, false if that time is already in the list
	def add_weekly_meeting(self, time: datetime.datetime) -> bool:
		# if the meeting list is empty, just add the meeting to the list
		if len(self.meetings) == 0:
			self.weekly_meetings.append(time)
		# if there's only 1 item in the list
		elif len(self.weekly_meetings) == 1:
			if time < self.weekly_meetings[0]:
				self.weekly_meetings.insert(0, time)
			elif time > self.weekly_meetings[0]:
				self.weekly_meetings.append(time)
			# if the time is a duplicate
			else:
				return False
		# if the list has at least 2 meetings, do a binary insert
		else:
			# start by checking entire list
			low = 0
			high = len(self.weekly_meetings) - 1
			# while there are more than 2 more list items to check
			while high - low > 1:
				# get mid point of remaining list to check
				mid = (high - low) // 2 + low
				# if the time is less than the mid point, remove the upper half of the remaining list to check
				if time.weekday() < self.weekly_meetings[mid].weekday():
					high = mid - 1
				# if the time is greater than the mid point, remove the lower half of the remaining list to check
				elif time.weekday() > self.weekly_meetings[mid].weekday():
					low = mid + 1
				# if the time is a duplicate
				else:
					return False
			
			# if the time is between the last 2 items
			if time.weekday() > self.weekly_meetings[low].weekday() and time.weekday() < self.weekly_meetings[high].weekday():
				# insert the time between those 2 items
				self.weekly_meetings.insert(high, time)
			# if the time is less than the lower last item
			elif time.weekday() < self.weekly_meetings[low].weekday():
				# insert the time in front of that item
				self.weekly_meetings.insert(low, time)
			# if the time is greater than the higher last item
			elif time.weekday() > self.weekly_meetings[high].weekday():
				# insert the time after that item
				self.weekly_meetings.insert(high + 1, time)
			# if the time is equal to one of those times
			else:
				return False
		
		return True
	
	# adds a birthday to the bday list in sorted order with a binary search
	# returns true if the bday was added to the list, false if a bday on the same day for the same name is already in the list
	def add_bday(self, bday: BDay) -> bool:
		# if the bday is empty, just add the bday to the list
		if len(self.bdays) == 0:
			self.bdays.append(bday)
		# if there's only 1 item in the list
		elif len(self.bdays) == 1:
			if bday.date < self.bdays[0].date:
				self.bdays.insert(0, bday)
			elif bday.date > self.bdays[0].date:
				self.bdays.append(bday)
			# if the bday is on the same day but has a different name
			elif bday.name != self.bdays[0].name:
				self.bdays.append(bday)
			# if the bday is on the same day and has the same name as the other bday
			else:
				return False
		# if the list has at least 2 bdays, do a binary insert
		else:
			# start by checking entire list
			low = 0
			high = len(self.bdays) - 1
			# while there are more than 2 more list items to check
			while high - low > 1:
				# get mid point of remaining list to check
				mid = (high - low) // 2 + low
				# if the date is less than the mid point, remove the upper half of the remaining list to check
				if bday.date < self.bdays[mid].date:
					high = mid - 1
				# if the date is greater than the mid point, remove the lower half of the remaining list to check
				elif bday.date > self.bdays[mid].date:
					low = mid + 1
				# if the bday is a duplicate
				else:
					return False
			
			# if the date is between the last 2 items
			if bday.date > self.bdays[low].date and bday.date < self.bdays[high].date:
				# insert the bday between those 2 items
				self.bdays.insert(high, bday)
			# if the date is less than the lower last item
			elif bday.date < self.bdays[low].date:
				# insert the bday in front of that item
				self.bdays.insert(low, bday)
			# if the date is greater than the higher last item
			elif bday.date > self.bdays[high].date:
				# insert the bday after that item
				self.bdays.insert(high + 1, bday)
			# if the bday is on the same day as another one but has a different name
			elif bday.name != self.bdays[low].name or bday.name != self.bdays[high].name:
				# insert the bday at the higher bday
				self.bdays.insert(high, bday)
			# if the bday is on the same day and has the same name as another bday
			else:
				return False
		
		return True
	
	# removes meetings from the server's list of meetings given a list of arguments of the meetings' numbers
	# returns true if all of the meetings were successfully removed, returns false if any of the meeting numbers wasn't valid
	def remove_meetings(self, meeting_numbers: list) -> bool:
		meeting_indexes = []
		# loop through each argument
		for arg in meeting_numbers:
			# if the argument is a positive integer
			if arg.isnumeric():
				# turn the argument into a number
				index = int(arg)
				# if the number is between 1 and the last weekly meeting number
				if index >= 1 and index  <= len(self.meetings):
					# add that number to a list of indexes to remove
					meeting_indexes.append(index)
					continue
			
			# if any of the arguments aren't valid
			return False
		
		# sort the list of indexes in reverse order because the right indexes will change while they're being removed if they're iterated through ascending order
		meeting_indexes.sort(reverse=True)
		# remove each meeting from the list in reverse order
		for i in meeting_indexes:
			self.meetings.pop(i - 1)
		
		return True
	
	# removes weekly meetings from the server's list of weekly meetings given a list of arguments of the meetings' numbers
	# returns true if all of the meetings were successfully removed, returns false if any of the meeting numbers wasn't valid
	def remove_weekly_meetings(self, meeting_numbers: list) -> bool:
		meeting_indexes = []
		# loop through each argument
		for arg in meeting_numbers:
			# if the argument is a positive integer
			if arg.isnumeric():
				# turn the argument into a number
				index = int(arg)
				# if the number is between 1 and the last weekly meeting number
				if index >= 1 and index  <= len(self.weekly_meetings):
					# add that number to a list of indexes to remove
					meeting_indexes.append(index)
					continue
			
			# if any of the arguments aren't valid
			return False
		
		# sort the list of indexes in reverse order because the right indexes will change while they're being removed if they're iterated through ascending order
		meeting_indexes.sort(reverse=True)
		# remove each meeting from the list in reverse order
		for i in meeting_indexes:
			self.weekly_meetings.pop(i - 1)
		
		return True
	
	# removes a birthday from the server's list of birthdays given a bday object
	# returns true if the bday was found and removed, false if it wasn't
	def remove_bday(self, bday: BDay) -> bool:
		# if the bday is in the list
		if bday in self.bdays:
			# remove it from the list and return true
			index = self.bdays.index(bday)
			self.bdays.pop(index)
			return True
		# if the bday is not in the list
		else:
			return False
	
	# sets the agenda notetaking order to a given list of names
	def set_agenda_order(self, names: list):
		self.agenda_order = names
		self.agenda_index = 0
	
	# sets the meeting minutes notetaking order to a given list of names
	def set_minutes_order(self, names: list):
		self.minutes_order = names
		self.minutes_index = 0
	
	# sets the agenda index to the inputted name at that index
	# returns true if the name was found, false if it wasn't
	def set_agenda_to(self, name: str) -> bool:
		if name in self.agenda_order:
			self.agenda_index = self.agenda_order.find(name)
			return True
		else:
			return False
	
	# sets the minutes index to the inputted name at that index
	# returns true if the name was found, false if it wasn't
	def set_minutes_to(self, name: str) -> bool:
		if name in self.minutes_order:
			self.minutes_index = self.minutes_order.find(name)
			return True
		else:
			return False
	
	# sets the agenda duty list to an empty list and the agenda index to 0
	def clear_agenda_order(self):
		self.agenda_order = []
		self.agenda_index = 0
	
	# sets the meeting minutes duty list to an empty list and the minutes index to 0
	def clear_minutes_order(self):
		self.minutes_order = []
		self.minutes_index = 0
	
	# returns the first text channel that the bot has permission to send messages in, returns none if there are none
	def find_first_message_channel(self):
		for channel in self.server.text_channels:
			channel_perms = channel.permissions_for(self.server.me)
			if channel_perms.send_messages:
				return channel
		
		return None

########################################################################################################################
#
# startup instructions
#
########################################################################################################################

# discord bot permissions
perms = discord.Intents.default()
perms.message_content = True

# sets up the bot client
client = discord.Client(intents = perms)

# gets the secret bot token by reading it from a local txt file
with open("token.txt", "r") as file:
	bot_token = file.readline().strip()

# strings for the bot to detect commands
desktop_prefix = ""
mobile_prefix = ""

# root directory of all server data
server_root = 'servers'

# used for keeping track of each server's meeting / dutyorders etc.
# maps a discord guild object to a ServerData object
server_data = {}

# flag to signal if a server is done setting up
running = False

# called as soon as the bot is fully online and operational
@client.event
async def on_ready():
	# strings that go at the start of commands to help the bot detect the command
	# it is currently "@{botname}"
	global desktop_prefix
	global mobile_prefix
	desktop_prefix = f"<@!{client.user.id}>"
	mobile_prefix = f"<@{client.user.id}>"

	# prints message to show that the bot is currently initializing the data for each server it's in
	print(datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), f"{sys.argv[0]}:", "Initializing server data...")

	# sets up and starts running the bot for each server it's in
	for server in client.guilds:
		await startup_server(server)
	
	# signal that the bot is done setting up
	global running
	running = True
	print(datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), f"{sys.argv[0]}:", "Bot is running")

########################################################################################################################
#
# server data handling
#
########################################################################################################################

# sets up all of the data for a server when it joins one or the bot starts running
async def startup_server(server):
	# create necessary folders and files if they don't already exist

	# gets the path to the server's data folder
	server_folder = get_server_folder_name(server)
	# path to server's data files
	data_files = []
	meetings_file = f'{server_folder}/meetings.lst'
	data_files.append(meetings_file)
	weekly_file = f'{server_folder}/weekly_meetings.lst'
	data_files.append(weekly_file)
	agenda_file = f'{server_folder}/agenda_order.lst'
	data_files.append(agenda_file)
	minutes_file = f'{server_folder}/minutes_order.lst'
	data_files.append(minutes_file)
	alert_file = f'{server_folder}/alert_channel.lst'
	data_files.append(alert_file)
	bdays_file = f'{server_folder}/bdays.lst'
	data_files.append(bdays_file)

	# if the server folder doesn't exist, make one
	if not os.path.isdir('servers'):
		os.mkdir('servers')
	# if the folder for this server's data doesn't exist, make it
	if not os.path.isdir(server_folder):
		os.mkdir(server_folder)
	# if any of the server's data files don't exist, make them
	for file in data_files:
		if not os.path.isfile(file):
			Path(file).touch()
	
	# initialize this server's data
	# TODO: make it so this reads from files instead of initializing everything to nothing
	server_data[server] = ServerData(server)

# sets up the bot for a new server every time it joins one while running
@client.event
async def on_guild_join(server):
	await startup_server(server)

# removes all of a server's data when the bot leaves a server
@client.event
async def on_guild_remove(server):
	# removes server's data from the server_data list of it's in there
	if server in server_data:
		server_data.pop(server)

	# TODO: make it so the bot hangs onto a server's data for a day before it deletes it
	# gets the path to the server's data folder
	server_folder = get_server_folder_name(server)
	# deletes the folder and all files in it if the folder exists
	if os.path.isdir(server_folder):
		shutil.rmtree(server_folder)

# returns the path to a server's data folder
def get_server_folder_name(server) -> str:
	# get server's name up to 128 chars
	server_name = server.name[:128]
	# turn all illegal filename chars in the name to underscores
	illegal_chars = ['#', '%', '&', '{', '}', '\\', '<', '>', '*', '?', '/', ' ', '$', '!', '\'', '"', ':', '@', '+', '`', '|', '=']
	for c in illegal_chars:
		server_name = server_name.replace(c, '_')
	# server's data folder path
	server_folder = f'{server_root}/{server.id}-{server_name}'
	return server_folder

########################################################################################################################
#
# command detection
#
########################################################################################################################

# returns true if a message is a command, false if it isn't
async def is_command(message) -> bool:
	# if the message is not a DM, not from itself (prevents recursion), and starts with a command prefix
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
	# if the bot is done setting up, the message is a command from a valid source, and it starts with a command prefix
	if running and await is_command(message):
		# splits the command up into tokens by whitespace
		command = message.content.split()
		# remove the prefix from the command list
		command.pop(0)
		# if there is a command
		if len(command) > 0:
			# turns the first token (command type) into all lowercase so it's easier and faster to check the command type
			command[0] = command[0].lower()
			# if it's the help command
			if command[0] == 'help':
				if len(command) > 1:
					await help_command(message, command[1])
				else:
					await help_command(message)
			# if it's the add meeting command
			elif command[0] == 'add':
				await add_command(message, command)
			# if it's the remove meeting command
			elif command[0] == 'remove':
				await remove_command(message, command)
			# if it's the show meetings command
			elif command[0] == 'meetings':
				await meetings_command(message)
			# if it's the set notetaking order command
			elif command[0] == 'set':
				await set_command(message, command)
			# if it's the dutyorder command
			elif command[0] == 'dutyorder':
				await dutyorder_command(message)
			# if it's the alert command
			elif command[0] == 'alert':
				await alert_command(message, command)
			# if it's the bdays command
			elif command[0] == 'bdays':
				await bdays_command(message)
			else:
				await help_command(message)
		# if the bot was @'d with no command
		else:
			await help_command(message)

########################################################################################################################
#
# command handling
#
########################################################################################################################

# handles the help command that displays a message about how to use commands
async def help_command(message, command = ''):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to send messages in the channel of the message
	if channel_perms.send_messages:
		command = command.lower()
		# if info on the help command was requested
		if command == 'help':
			# list of string lines that the bot will reply to the help command with
			help_reply = f'`{command}:` Gives info about the bot and it\'s commands.\n\n'

			help_reply += '```Usages:```\n'

			help_reply += f'**{desktop_prefix} help**\n'
			help_reply += 'This will print out the default help message that shows how to use the bot and lists all of the bot\'s commands.\n\n'

			help_reply += f'**{desktop_prefix} help [command]**\n'
			help_reply += 'Gives info on [command].\n'

			help_reply += '\n```Examples:```\n'

			help_reply += f'{desktop_prefix} help\n'
			help_reply += f'{desktop_prefix} help add\n'
			help_reply += f'{desktop_prefix} help meetings'

			await safe_reply(message, help_reply)
		# if the info on the add command was requested
		elif command == 'add':
			# list of string lines that the bot will reply to the help command with
			help_reply = f'`{command}:` Adds a meeting or a birthday to the bot so it can remind you about it.\n\n'

			help_reply += '```Usages:```\n'

			help_reply += f'**{desktop_prefix} add meeting on [date] at [time]**\n'
			help_reply += 'This will add a meeting to the bot, and the bot will remind you about the meeting on [date] a few minutes before [time] and then forget about it.\n'
			help_reply += 'Note: you cannot add a meeting with the exact same time and date as an already existing meeting.\n\n'

			help_reply += f'**{desktop_prefix} add weekly meeting on [day] at [time]**\n'
			help_reply += 'This will add a meeting to the bot that recurs every week, and the bot will remind you about the meeting every week on [day] a few minutes before [time].\n'
			help_reply += 'Note: you cannot add a weekly meeting with the exact same time and day as an already existing weekly meeting.\n\n'

			help_reply += f'**{desktop_prefix} add bday on [date] for [name]**\n'
			help_reply += 'This will add a birthday to the bot, and the bot will say happy birthday on [date] to [name].\n'
			help_reply += 'Note: you cannot add a birthday for a person with the exact same name and date as an already existing birthday.\n\n'

			help_reply += '**Formatting:**\n\n'
			help_reply += '**[date]:** YYYY/M/D or YYYY-M-D M/D or M-D (YYYY = year (1 <= YYYY <= 9999), M = month (1 <= M <= 12), D = day (1 <= D <= 31)).\n'
			help_reply += 'Note: if the year is not inputted in the date, the next available date on M/D will be inputted. The bot will ignore years on bday inputs.\n'
			help_reply += '**[time]:** H:M or H:M am/pm or H or H am/pm (H = hour (1 <= H <= 12 or 1 <= H <= 24), M = minute (1 <= M <= 59)).\n'
			help_reply += '**[day]:** Sundays: (su, sun, sunday, sundays), Mondays: (m, mon, monday, mondays), Tuesdays: (tu, tue, tues, tuesday, tuesdays), '
			help_reply += 'Wednesdays: (w, wed, wednesday, wednesdays), Thursdays: (th, thu, thur, thurs, thursday, thursdays), Fridays: (f, fri, friday, fridays), '
			help_reply += 'Saturdays: (sa, sat, saturdays, saturdays).\n\n'

			help_reply += '```Examples:```\n'

			help_reply += f'{desktop_prefix} add meeting on 11/15 at 10:30 am\n'
			help_reply += f'{desktop_prefix} add weekly meeting on tu at 15:30\n'
			help_reply += f'{desktop_prefix} add bday on 1/7 for Chandler\n'
			help_reply += f'{desktop_prefix} add meeting on 9-20 at 4 pm\n'
			help_reply += f'{desktop_prefix} add weekly meeting on mondays at 18\n'
			help_reply += f'{desktop_prefix} add bday on 12-1 for Josh\n'
			help_reply += f'{desktop_prefix} add meeting on 2024/10/31 at 1 am\n'
			help_reply += f'{desktop_prefix} add weekly meeting on friday at 1:45 pm\n'
			help_reply += f'{desktop_prefix} add bday on 4/1 for Francis Fulloffrenchpeople'

			await safe_reply(message, help_reply)
		# if the info on the remove command was requested
		elif command == 'remove':
			# list of string lines that the bot will reply to the help command with
			help_reply = f'`{command}:` Removes a meeting, a birthday, or clear the agenda or meeting minutes duty list from the bot.\n\n'

			help_reply += '```Usages:```\n'

			help_reply += f'**{desktop_prefix} remove meeting [meeting number(s)]**\n'
			help_reply += 'This will remove the meeting(s) with the numbers [meeting number(s)].\n'
			help_reply += 'Note: You can find a meeting\'s number with the "meetings" command (it\'s the number to the left of the meeting).\n\n'

			help_reply += f'**{desktop_prefix} remove meetings [meeting number(s)]**\n'
			help_reply += 'Same as above.\n\n'

			help_reply += f'**{desktop_prefix} remove weekly meeting [meeting number(s)]**\n'
			help_reply += 'This will remove the weekly meeting(s) with the numbers [meeting number(s)].\n'
			help_reply += 'Note: You can find a meeting\'s number with the "meetings" command (it\'s the number to the left of the meeting).\n\n'

			help_reply += f'**{desktop_prefix} remove weekly meetings [meeting number(s)]**\n'
			help_reply += 'Same as above.\n\n'

			help_reply += f'**{desktop_prefix} remove agenda**\n'
			help_reply += 'Clears the agenda notetaking duty list.\n\n'

			help_reply += f'**{desktop_prefix} remove minutes**\n'
			help_reply += 'Clears the meeting minutes notetaking duty list.\n\n'

			help_reply += f'**{desktop_prefix} remove bday on [date] for [name]**\n'
			help_reply += 'This will remove a birthday on [date] for the person named [name].\n'
			help_reply += 'Note: You can see which birthdays have been added with the "bdays" command.\n\n'

			help_reply += '**Formatting:**\n\n'
			help_reply += '**[date]:** M/D or M-D (M = month (1 <= M <= 12), D = day (1 <= D <= 31)).\n\n'

			help_reply += '```Examples:```\n'

			help_reply += f'{desktop_prefix} remove meeting 1\n'
			help_reply += f'{desktop_prefix} remove weekly meeting 2 6 4\n'
			help_reply += f'{desktop_prefix} remove agenda\n'
			help_reply += f'{desktop_prefix} remove bday on 1/7 for Chandler\n'
			help_reply += f'{desktop_prefix} remove meetings 7 3 5\n'
			help_reply += f'{desktop_prefix} remove weekly meetings 8\n'
			help_reply += f'{desktop_prefix} remove minutes\n'
			help_reply += f'{desktop_prefix} remove bday on 12-1 for Josh\n'

			await safe_reply(message, help_reply)
		# if the info on the meetings command was requested
		elif command == 'meetings':
			# list of string lines that bot will reply to the help command with
			help_reply = f'`{command};` Displays all meetings and weekly meetings.\n\n'

			help_reply += '```Usage:```\n'

			help_reply += f'**{desktop_prefix} meetings**\n'
			help_reply += 'This will display all meetings and weekly meetings that the bot is currently storing along with each meeting\'s removal number.\n'
			help_reply += 'Note: See how to use the meeting removal numbers and remove meetings in the "remove" command info, as well as how to add '
			help_reply += 'meetings in the "add" command info.'

			await safe_reply(message, help_reply)
		# if the info on the set command was requested
		elif command == 'set':
			# list of string lines that the bot will reply to the help command with
			help_reply = f'`{command}:` Sets the agenda or meeting minutes notetaking order.\n\n'

			help_reply += '```Usages:```\n'

			help_reply += f'**{desktop_prefix} set agenda order as [name], [name], [name], ...**\n'
			help_reply += 'This will set the agenda notetaking order as the list of names at the end of the command.\n'
			help_reply += 'It will also reset the agenda notetaking list to start at the first name in this command and work it\'s way down.\n'
			help_reply += 'Every time there is a meeting, the bot will remind you whose turn it is on agenda, and after the meeting has started '
			help_reply += 'it will move onto the next person in the list for the next meeting.\n'
			help_reply += 'Note: See the current agenda order in the "dutyorder" command info.\n\n'

			help_reply += f'**{desktop_prefix} set minutes order as [name], [name], [name], ...**\n'
			help_reply += 'This will set the meeting minutes notetaking order as the list of names at the end of the command.\n'
			help_reply += 'It will also reset the meeting minutes notetaking list to start at the first name in this command and work it\'s way down.\n'
			help_reply += 'Every time there is a meeting, the bot will remind you whose turn it is on minutes, and after the meeting has started '
			help_reply += 'it will move onto the next person in the list for the next meeting.\n'
			help_reply += 'Note: See the current meeting minutes order in the "dutyorder" command info.\n\n'

			help_reply += f'**{desktop_prefix} set agenda to [name]**\n'
			help_reply += 'This will set the next person from the agenda list on agenda notetaking duty to [name].\n'
			help_reply += 'Note: See the current agenda order in the "dutyorder" command info.\n\n'

			help_reply += f'**{desktop_prefix} set minutes to [name]**\n'
			help_reply += 'This will set the next person from the minutes list on meeting minutes notetaking duty to [name].\n'
			help_reply += 'Note: See the current meeting minutes order in the "dutyorder" command info.\n\n'

			help_reply += '**Formatting:**\n\n'
			help_reply += 'Multiple names must be separated by commas.\n'

			help_reply += '```Examples:```\n'

			help_reply += f'{desktop_prefix} set agenda order as Chandler Glen Holly\n'
			help_reply += f'{desktop_prefix} set minutes order as Grant David Tyler\n'
			help_reply += f'{desktop_prefix} set agenda to Glen\n'
			help_reply += f'{desktop_prefix} set minutes to Tyler\n'

			await safe_reply(message, help_reply)
		# if the info on the dutyorder command was requested
		elif command == 'dutyorder':
			# list of string lines that the bot will reply to the help command with
			help_reply = f'`{command}:` Displays the current agenda and meeting minutes notetaking order.\n\n'

			help_reply += '```Usage:```\n'

			help_reply += f'**{desktop_prefix} dutyorder**\n'
			help_reply += 'This will display the current agenda and meeting minutes notetaking order, as well as who\'s next on each list.\n'
			help_reply += 'Note: See how to set the agenda and minutes orders in the "set" command info.'

			await safe_reply(message, help_reply)
		# if the info on the alert command was requested
		elif command == 'alert':
			# list of string lines that the bot will reply to the help command with
			help_reply = f'`{command}:` Sets the channel that the bot sends meeting and birthday alerts in and displays what the alert channel is set to.\n\n'

			help_reply += '```Usages:```\n'

			help_reply += f'**{desktop_prefix} alert here**\n'
			help_reply += 'This will set the channel that the bot sends meeting and birthday alerts in to the channel that the command was sent in.\n\n'

			help_reply += f'**{desktop_prefix} alert channel**\n'
			help_reply += 'This will display what channel the bot is currently using as the alert channel.'

			await safe_reply(message, help_reply)
		# if the info on the bdays command was requested
		elif command == 'bdays':
			# list of string lines that the bot will reply to the help command with
			help_reply = f'`{command}:` Displays all birthdays the bot is currently keeping track of.\n\n'

			help_reply += '```Usage:```\n'

			help_reply += f'**{desktop_prefix} bdays**\n'
			help_reply += 'This will display all birthdays that the bot is currently keeping track of to say happy birthday to.\n'
			help_reply += 'Note: See how to add and remove birthdays in the "add" and "remove" command infos.'

			await safe_reply(message, help_reply)
		# if no argument was given or it isn't recognized
		else:
			# list of commands that the bot has
			command_list = ['help', 'add', 'remove', 'meetings', 'set', 'dutyorder', 'alert', 'bdays']
			# list of string lines that the bot will reply to the help command with
			help_reply = f'`Usage:` **{desktop_prefix} [command] [arguments...]**\n\n'
			help_reply += f'Type "{desktop_prefix} help [command]" to get more info on how to use a specific command.\n\n'
			help_reply += f'```List of commands:```\n'
			# add a numbered line for each command the bot has
			for i in range(len(command_list)):
				help_reply += f'**{i + 1}. {command_list[i]}**\n'
			
			await safe_reply(message, help_reply)
	# if the bot doesn't have permission to send message in the channel, react to the message with an x
	else:
		await react_with_x(message)

# handles the add command that adds meetings to the server's meeting list
async def add_command(message, command):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to add reactions in this channel
	if channel_perms.add_reactions:
		# if the command follows the format "add meeting on *day* at *time"
		if len(command) > 5 and command[1].lower() == 'meeting' and command[2].lower() == 'on' and command[4].lower() == 'at':
			# extract date
			date_nums = str_to_date_nums(command[3])
			# if the inputted date is invalid
			if date_nums is None:
				await react_with_x(message)
				return
			
			# put date_num variables into more recognizable variable names
			year, month, day = date_nums
			
			# extract time

			# if the command has a "pm" or "am" after the time
			if len(command) > 6:
				# extract 12 hour time string into 24 hour time numbers
				hour, minute = str_to_time_12hr(command[5], command[6])
			else:
				# extract 24 hour time string into numbers
				hour, minute = str_to_time_24hr(command[5])
			# if a valid time was not inputted
			if hour is None:
				await react_with_x(message)
				return
			
			# construct datetime object

			# if the year wasn't inputted
			if year is None:
				if valid_date(day, month):
					now = datetime.datetime.now()
					meeting = datetime.datetime(now.year, month, day, hour=hour, minute=minute)
					# if the meeting date is before now, increment it by a year
					if meeting < now:
						meeting = datetime.datetime(now.year + 1, month, day, hour=hour, minute=minute)
				else:
					await react_with_x(message)
					return
			# if a year was inputted
			else:
				if valid_date(day, month, year=year):
					meeting = datetime.datetime(year, month, day, hour=hour, minute=minute)
					now = datetime.datetime.now()
					if meeting < now:
						await react_with_x(message)
						return
			
			# add meeting to list

			# if the meeting time is successfully added to the list in order and is not a duplicate
			if server_data[message.guild].add_meeting(meeting):
				await react_with_check(message)
			else:
				await react_with_x(message)
		# if the command follows the format "add weekly meeting on *day* at *time*"
		elif len(command) > 6 and command[1].lower() == 'weekly' and command[2].lower() == 'meeting' and command[3].lower() == 'on' and command[5].lower() == 'at':
			# extract day

			# get a number 0 to 6 of the day of the week
			day = day_to_num(command[4])
			# if a valid day of the week was not inputted
			if day is None:
				await react_with_x(message)
				return
			
			# extract time

			# if the command has a "pm" or "am" after the time
			if len(command) > 7:
				# extract 12 hour time string into 24 hour time numbers
				hour, minute = str_to_time_12hr(command[6], command[7])
			else:
				# extract 24 hour time string into numbers
				hour, minute = str_to_time_24hr(command[6])
			# if a valid time was not inputted
			if hour is None:
				await react_with_x(message)
				return
			
			# convert weekday to next datetime on that weekday

			# set meeting time to today at the inputted hour and minute by default
			now = datetime.datetime.now()
			meeting_time = datetime.datetime(now.year, now.month, now.day, hour=hour, minute=minute)
			# if the meeting weekday is later in the week
			if day > now.weekday():
				# set the meeting time to the right day later this week
				delta = datetime.timedelta(days=(day - now.weekday()))
				meeting_time += delta
			# if the meeting weekday is earlier in the week or on the same day but at an earlier time in the day
			elif day < now.weekday() or (day == now.weekday() and (hour < now.hour or (hour == now.hour and minute <= now.minute))):
				# set the meeting time to the right day next week
				meeting_time = datetime.datetime(now.year, now.month, now.day, hour=hour, minute=minute)
				delta = datetime.timedelta(days=(7 - now.weekday() + day))
				meeting_time += delta
			
			# add day and time to list

			# if the meeting time is successfully added to the list in order and is not a duplicate
			if server_data[message.guild].add_weekly_meeting(meeting):
				await react_with_check(message)
			else:
				await react_with_x(message)
		
		# if the command follows the format "add bday on *day*"
		elif len(command) > 5 and command[1].lower() == 'bday' and command[2].lower() == 'on' and command[4].lower() == 'for':
			# extract date
			date_nums = str_to_date_nums(command[3])
			if date_nums is None:
				await react_with_x(message)
				return
			
			# put date_num variables into more recognizable variable names
			year, month, day = date_nums

			# construct datetime object

			# time of the day that the bot will alert people about the birthday
			hour = 8
			minute = 0

			# if the year wasn't inputted
			if year is None:
				if valid_date(day, month):
					now = datetime.datetime.now()
					meeting = datetime.datetime(now.year, month, day, hour=hour, minute=minute)
					# if the meeting date is before now, increment it by a year
					if meeting < now:
						meeting = datetime.datetime(now.year + 1, month, day, hour=hour, minute=minute)
				else:
					await react_with_x(message)
					return
			# if a year was inputted
			else:
				await react_with_x(message)
				return
			
			# create bday object
			bday = BDay(meeting, ' '.join(command[5:]))
			# if the bday was successfully added to the bday list
			if server_data[message.guild].add_bday(bday):
				await react_with_check(message)
			# if the bday is a duplicate (same name and date as an existing one)
			else:
				await react_with_x(message)
		# if the command isn't recognized
		else:
			await react_with_x(message)

# handles the remove meeting command
async def remove_command(message, command):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to add reactions in this channel
	if channel_perms.add_reactions:
		# if the command follows the format "remove meeting(s) # # # ..."
		if len(command) > 2 and (command[1].lower() == 'meeting' or command[1].lower() == 'meetings'):
			# remove the meetings with the inputted numbers if all of the inputted numbers are valid
			if server_data[message.guild].remove_meetings(command[2:]):
				await react_with_check(message)
			# if any of the inputted numbers are not valid
			else:
				await react_with_x(message)
		# if the command follows the format "remove weekly meeting(s) # # # ..."
		elif len(command) > 3 and command[1].lower() == 'weekly' and (command[2].lower() == 'meeting' or command[2].lower() == 'meetings'):
			# remove the weekly meetings with the inputted numbers if all of the inputted numbers are valid
			if server_data[message.guild].remove_weekly_meetings(command[3:]):
				await react_with_check(message)
			# if any of the inputted numbers are not valid
			else:
				await react_with_x(message)
		# if the command follows the format "remove agenda"
		elif len(command) > 1 and command[1].lower() == 'agenda':
			# clear the server's agenda duty list
			server_data[message.guild].clear_agenda_order()
			await react_with_check(message)
		# if the command follows the format "remove minutes"
		elif len(command) > 1 and command[1].lower() == 'minutes':
			# clear the server's meeting minutes duty list
			server_data[message.guild].clear_minutes_order()
			await react_with_check(message)
		# if the command follows the format "remove bday on [date] for [name]"
		elif len(command) > 5 and command[1].lower() == 'bday' and command[2].lower() == 'on' and command[4].lower() == 'for':
			# extract date
			date_nums = str_to_date_nums(command[3])
			if date_nums is None:
				await react_with_x(message)
				return
			
			# put date_num variables into more recognizable variable names
			year, month, day = date_nums

			# construct datetime object

			# time of the day that the bot will alert people about the birthday
			hour = 8
			minute = 0

			# if the year wasn't inputted
			if year is None:
				if valid_date(day, month):
					now = datetime.datetime.now()
					meeting = datetime.datetime(now.year, month, day, hour=hour, minute=minute)
					# if the meeting date is before now, increment it by a year
					if meeting < now:
						meeting = datetime.datetime(now.year + 1, month, day, hour=hour, minute=minute)
				else:
					await react_with_x(message)
					return
			# if a year was inputted
			else:
				await react_with_x(message)
				return
			
			# create bday object
			bday = BDay(meeting, ' '.join(command[5:]))
			# if the bday was successfully removed from the bday list
			if server_data[message.guild].remove_bday(bday):
				await react_with_check(message)
			# if the bday wasn't found / successfully removed from the list
			else:
				await react_with_x(message)
		# if the command isn't recognized
		else:
			await react_with_x(message)

# handles the meetings command that shows all current meetings
async def meetings_command(message):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to send messages in the channel of the message
	if channel_perms.send_messages:
		reply = '```One-Time Meetings```\n'
		
		# if there are no one time meetings
		if len(server_data[message.guild].meetings) < 1:
			reply += '**No meetings.**\n\n'
		# if there is at least 1 meeting
		else:
			# display all of the meetings in a numbered list
			for i in range(len(server_data[message.guild].meetings)):
				# Why the actual fuck would you change the grammar of a damn language depending on the operating system
				# What. The. Fuck.
				# Who is responsible for making this function and how the fuck were they allowed to contribute to python in the first place
				# What else has this individual / these individuals fucked up with this language
				# Linux version:
				# meeting_str = server_data[message.guild].meetings[i].strftime('%A %b %-d %Y at %-H:%M / %-I:%M %p')
				# Windows version:
				meeting_str = server_data[message.guild].meetings[i].strftime('%A %b %#d %Y at %#H:%M / %#I:%M %p')
				reply += f'**{i+1}. {meeting_str}**\n\n'

		reply += '```Weekly Meetings```\n'

		# if there are no weekly meetings
		if len(server_data[message.guild].weekly_meetings) < 1:
			reply += '**No weekly meetings.**\n'
		# if there is at least 1 weekly meeting
		else:
			# display all of the weekly meetings in a numbered list
			for i in range(len(server_data[message.guild].weekly_meetings)):
				# Linux version:
				# meeting_str = server_data[message.guild].weekly_meetings[i].strftime('%As at %-H:%M / %-I:%M %p')
				# Windows version:
				meeting_str = server_data[message.guild].weekly_meetings[i].strftime('%As at %#H:%M / %#I:%M %p')
				reply += f'**{i+1}. {meeting_str}**\n\n'
		
		await safe_reply(message, reply)
	# if the bot doesn't have permission to send message in the channel, react to the message with an x
	else:
		await react_with_x(message)

# handles the set command that sets the order of agenda and meeting minutes notetaking duty
async def set_command(message, command):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to send messages in the channel of the message
	if channel_perms.add_reactions:
		# if user wants to remake a list
		if len(command) > 4 and command[2].lower() == 'order' and command[3].lower() == 'to':
			# set the 'agenda' / 'minutes' argument to all lowercase for easy comparison later
			command[1] = command[1].lower()
			# rebuild the list of names as a string
			name_list = ' '.join(command[4:])
			
			# split the list of names by commas
			name_list = name_list.split(',')
			# iterate backwards through the name list (since some items might be removed)
			for i in range(len(name_list)-1, -1, -1):
				# if an item is an empty string or only whitespace, remove it
				if name_list[i] == '' or name_list[i].isspace():
					name_list.pop(i)
				# if it isn't an empty string
				else:
					# remove surrounding whitespace
					name_list[i] = name_list[i].strip()
					# if the name is a duplicate
					dupe = name_list.copy()
					dupe.pop(i)
					if name_list[i] in dupe:
						await react_with_x(message)
						return
			
			# if agenda list was passed as an argument, set the agenda list to the new list
			if command[1] == 'agenda':
				server_data[message.guild].set_agenda_order(name_list)
			# if the minutes list was passed as an argument, set the agenda list to the new list
			elif command[1] == 'minutes':
				server_data[message.guild].set_minutes_order(name_list)
			# if the argument isn't recognized
			else:
				await react_with_x(message)
				return
			
			await react_with_check(message)
		# if the user wants to skip to a person on the list
		elif len(command) > 3 and command[2].lower() == 'to':
			# set the 'agenda' / 'minutes' argument to all lowercase for easy comparison later
			command[1] = command[1].lower()
			# if the agenda list was passed as an argument
			if command[1] == 'agenda':
				# rebuild the name of the person passed as an argument into a string
				name = command[3]
				for token in command[4:]:
					name += ' ' + token
				
				# if that name is in the agenda list
				if server_data[message.guild].set_agenda_to(name):
					await react_with_check(message)
				else:
					await react_with_x(message)
			# if the minutes list was passed as an argument
			elif command[1] == 'minutes':
				# rebuild the name of the person passed as an argument into a string
				name = command[3]
				for token in command[4:]:
					name += ' ' + token
				
				# if that name is in the minutes list
				if server_data[message.guild].set_minutes_to(name):
					await react_with_check(message)
				else:
					await react_with_x(message)
			else:
				await react_with_x(message)
		# if the command is not valid
		else:
			await react_with_x(message)

# handles the dutyorder command that shows the current agenda and meeting minutes order
async def dutyorder_command(message):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to send messages in the channel of the message
	if channel_perms.send_messages:
		up_next = '  <-- Up Next'
		reply = '```Agenda Duty:```\n'
		
		# if the agenda duty list is empty
		if len(server_data[message.guild].agenda_order) < 1:
			reply += '**No agenda duty list**\n\n'
		# if there is anyone on the agenda duty list
		else:
			# display the list of people on agenda duty
			for i in range(len(server_data[message.guild].agenda_order)):
				reply += f'**{i + 1}. {server_data[message.guild].agenda_order[i]}**'
				# if the person that was just printed is up next, put an arrow and some text next to their name to say so
				if i == server_data[message.guild].agenda_index:
					reply += up_next
				
				reply += '\n\n'
		
		reply += '```Meeting Minutes Duty:```\n'

		# if the meeting minutes duty list is empty
		if len(server_data[message.guild].minutes_order) < 1:
			reply += '**No meeting minutes duty list**'
		# if there is anyone on the meeting minutes duty list
		else:
			# display the list of people on meeting minutes duty
			for i in range(len(server_data[message.guild].minutes_order)):
				reply += f'**{i + 1}. {server_data[message.guild].minutes_order[i]}**'
				# if the person that was just printed is up next, put an arrow and some text next to their name to say so
				if i == server_data[message.guild].minutes_index:
					reply += up_next
				
				reply += '\n\n'
		
		await safe_reply(message, reply)
	# if the bot doesn't have permission to send message in the channel of the message
	else:
		await react_with_x(message)

# handles the alert command that sets the channel that people get alerted about meetings and bdays in
async def alert_command(message, command):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to send messages in the channel of the message
	if channel_perms.send_messages:
		# if the command has an argument
		if len(command) > 1:
			# set the argument to lowercase to make it easier to compare
			command[1] = command[1].lower()
			# if the command follows the format "alert here"
			if command[1] == 'here':
				# set the alert channel for the server to the one that the command was sent in
				server_data[message.guild].alert_channel = message.channel
				await react_with_check(message)
			# if the command follows the format "alert channel"
			elif command[1] == 'channel':
				# if the bot doesn't have an alert channel
				if server_data[message.guild].alert_channel is None:
					# look for one again
					server_data[message.guild].alert_channel = server_data[message.guild].find_first_message_server()
					# if the bot still can't find an alert channel
					if server_data[message.guild].alert_channel is None:
						await react_with_x(message)
						return
				
				# reply with the bot's alert channel
				reply = f'<#{server_data[message.guild].alert_channel.id}>'
				await safe_reply(message, reply)
		else:
			await react_with_x(message)
	else:
		await react_with_x(message)

# handles the bdays command that displays all birthdays that the bot is currently keeping track of
async def bdays_command(message):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to send messages in the channel of the message
	if channel_perms.send_messages:
		reply = '```Birthdays:```\n'

		# if the bday list is empty
		if len(server_data[message.guild].bdays) < 1:
			reply += '**No Birthdays**'
		# if the bday list has at least 1 item in it
		else:
			# display the list of bdays
			for bday in server_data[message.guild].bdays:
				reply += f'**{bday}**\n\n'

		await safe_reply(message, reply)
	else:
		await react_with_x(message)

########################################################################################################################
#
# command utility functions
#
########################################################################################################################

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

# replies to a message and handles lack of permissions and character overflow
async def safe_reply(message, reply: str):
	channel_perms = message.channel.permissions_for(message.guild.me)
	# if the bot has permission to send messages in the channel of the message
	if channel_perms.send_messages:
		max_message_len = 2000
		# while the reply is too long to send, find a split point before the message limit and send the reply up to that point
		while (len(reply) > max_message_len):
			# strings to split the reply at before the message limit
			split_strs = ["\n\n", "\n", " "]
			# index of where the reply will be split
			split_index = -1
			# loop through each substring to get the index of the last instance of one of the strings in split_strs in the relpy before the max message length
			for i in range(len(split_strs) + 1):
				# if all of the strings in split_strs have been checked and none of them were found, set the split_index to the max message length
				if i == len(split_strs):
					split_index = max_message_len + 1
				else:
					# find the index of the last instance of a string in split_strs
					split_index = reply.rfind(split_strs[i], 0, max_message_len)
					# if an instance of the string was found, use the index of that string as the split index
					if split_index != -1:
						split_index += 1
						break
			
			channel_perms = message.channel.permissions_for(message.guild.me)
			# check to make sure the bot still has permission to send messages in this channel
			if channel_perms.send_messages:
				# send the part of the reply up to the split index
				await message.reply(reply[:split_index])
			# if it doesn't, then stop and return
			else:
				return
			# remove the part of the reply that was just sent
			reply = reply[split_index:]
		
		channel_perms = message.channel.permissions_for(message.guild.me)
		# check to make sure the bot still has permission to send messages in this channel
		if channel_perms.send_messages:
			# send the remaining part of the reply that is less than the max message length
			await message.reply(reply)
	# if the bot doesn't have permission to send messages in the channel of the message, react with an x
	else:
		await react_with_x(message)

# turns a string of the format Y/M/D or Y-M-D into a tuple of numbers (year, month, day)
def str_to_date_nums(date: str):
	date_nums = []
	# if the date uses slashes
	if '/' in date and not '-' in date:
		# split the string by slashes
		date_nums = date.split('/')
	# if the date uses dashes
	elif '-' in date and not '/' in date:
		# split the string by dashes
		date_nums = date.split('-')
	# if the date argument either has both slashes and dashes or neither
	else:
		return None
	
	year = None
	month = None
	day = None
	# if there are exactly 2 strings from the split and they are both positive integers
	if len(date_nums) == 2 and date_nums[0].isnumeric() and date_nums[1].isnumeric():
		# convert those strings into numbers
		month = int(date_nums[0])
		day = int(date_nums[1])
	# if there are exactly 3 strings from the split and they are all positive integers
	elif len(date_nums) == 3 and date_nums[0].isnumeric() and date_nums[1].isnumeric() and date_nums[2].isnumeric():
		# convert those strings into numbers
		year = int(date_nums[0])
		month = int(date_nums[1])
		day = int(date_nums[2])
	# if the date input is invalid
	else:
		return None
	
	return (year, month, day)

# returns whether or not a string is a day of the week

def is_monday(token: str) -> bool:
	return token.lower() == 'm' or token.lower() == 'mon' or token.lower() == 'monday' or token.lower() == 'mondays'

def is_tuesday(token: str) -> bool:
	return token.lower() == 'tu' or token.lower() == 'tue' or token.lower() == 'tues' or token.lower() == 'tuesday' or token.lower() == 'tuesdays'

def is_wednesday(token: str) -> bool:
	return token.lower() == 'w' or token.lower() == 'wed' or token.lower() == 'wednesday' or token.lower() == 'wednesdays'

def is_thursday(token: str) -> bool:
	return token.lower() == 'th' or token.lower() == 'thu' or token.lower() == 'thur' or token.lower() == 'thurs' or token.lower() == 'thursday' or token.lower() == 'thursdays'

def is_friday(token: str) -> bool:
	return token.lower() == 'f' or token.lower() == 'fri' or token.lower() == 'friday' or token.lower() == 'fridays'

def is_saturday(token: str) -> bool:
	return token.lower() == 'sa' or token.lower() == 'sat' or token.lower() == 'saturday' or token.lower() == 'saturdays'

def is_sunday(token: str) -> bool:
	return token.lower() == 'su' or token.lower() == 'sun' or token.lower() == 'sunday' or token.lower() == 'sundays'

# converts a string of a day sunday to saturday to a number 0 to 6
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

# returns if a set of integers are valid for construction of a date object
def valid_date(day: int, month: int, year: int = datetime.MINYEAR) -> bool:
	if year < datetime.MINYEAR or year > datetime.MAXYEAR:
		return False
	elif month < 1 or month > 12:
		return False
	elif day < 1:
		return False
	elif month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12:
		if day > 31:
			return False
	elif month == 2:
		if day > 29:
			return False
	elif month == 4 or month == 6 or month == 9 or month == 11:
		if day > 30:
			return False
	
	return True

########################################################################################################################
#
# bot activation
#
########################################################################################################################

client.run(bot_token)