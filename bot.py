# used for interfacing with the discord api
import discord
# used for file io
import sys
import os
from pathlib import Path
import shutil
# used for storing and using date and time information
import datetime
from zoneinfo import ZoneInfo
# used for creating coroutine tasks so the bot can loop to check for time without freezing itself
import asyncio

########################################################################################################################
#
# global variables
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

# used for keeping track of each server's meeting / dutyorders etc.
# maps a discord guild object to a ServerData object
server_data = {}

# maximum number of characters that can be sent in a discord message
max_message_len = 2000

# timezone that the bot is running in (change this yourself if you want the bot to use another time zone)
timezone = ZoneInfo(key='US/Pacific')
# alternate for auto-using your machine's local timezone:
# timezone = ZoneInfo(key='localtime')

# string for displaying the current timezone in a nice way since %Z in datetime.strftime() doesn't work that well
# be sure to change this yourself as well if you using another timezone
tzstr = 'PT'

# string for displaying the contact info users can use to reach out if they have problems with the bot
contact_info = ""
if os.path.isfile("contact_info.txt"):
	with open("contact_info.txt", "r") as file:
		contact_info = file.readline().strip()

########################################################################################################################
#
# class definitions
#
########################################################################################################################

# class for storing data about weekly meetings for display purposes
class WeeklyMeeting:
	# constructor (day must be int between 0 and 6 (monday to sunday), hour must be int between 0 and 23, minute must be int between 0 and 59)
	def __init__(self, day: int, hour: int, minute: int):
		# if the day is valid
		if day >=0 and day <= 6:
			self.day = day
		else:
			raise ValueError(f'Day of the week must be int between 0 and 6, {day} is not')
		
		# if the hour is valid
		if hour >= 0 and hour <= 23:
			self.hour = hour
		else:
			raise ValueError(f'Hour must be int between 0 and 23, {hour} is not')
		
		# if the minute is valid
		if minute >= 0 and minute <= 59:
			self.minute = minute
		else:
			raise ValueError(f'Minute must be int between 0 and 59, {minute} is not')
		
		# string for displaying the day of the week
		if day == 0:
			self.day_str = 'Monday'
		elif day == 1:
			self.day_str = 'Tuesday'
		elif day == 2:
			self.day_str = 'Wednesday'
		elif day == 3:
			self.day_str = 'Thursday'
		elif day == 4:
			self.day_str = 'Friday'
		elif day == 5:
			self.day_str = 'Saturday'
		elif day == 6:
			self.day_str = 'Sunday'
		else:
			raise ValueError(f'Day of the week must be int between 0 and 6, {day} is not')
		
		# hour in 12 hour time instead of 24 and am / pm
		if hour > 12:
			self.hour_12 = hour - 12
			self.ampm = 'pm'
		elif hour == 0:
			self.hour_12 = 12
			self.ampm = 'am'
		else:
			self.hour_12 = hour
			if hour == 12:
				self.ampm = 'pm'
			else:
				self.ampm = 'am'
		
		# string for displaying minute with a 0 padded onto numbers with only one digit
		if minute < 10:
			self.min_str = '0' + str(minute)
		else:
			self.min_str = str(minute)
	
	# string caster
	def __str__(self):
		return f'{self.day_str}s at {self.hour}:{self.min_str} / {self.hour_12}:{self.min_str} {self.ampm} {tzstr}'
	
	###########################################################################
	#
	# operator overloads
	#
	###########################################################################

	# equal ==
	def __eq__(self, other) -> bool:
		if type(other) is WeeklyMeeting:
			return self.day == other.day and self.hour == other.hour and self.minute == other.minute
		elif type(other) is datetime.datetime:
			return self.day == other.weekday() and self.hour == other.hour and self.minute == other.minute
		else:
			raise TypeError(f'WeeklyMeeting class does not support operations with {type(other)}, only other WeeklyMeetings and datetimes')
	
	# not equal !=
	def __ne__(self, other) -> bool:
		if type(other) is WeeklyMeeting:
			return self.day != other.day or self.hour != other.hour or self.minute != other.minute
		elif type(other) is datetime.datetime:
			return self.day != other.weekday() or self.hour != other.hour or self.minute != other.minute
		else:
			raise TypeError(f'WeeklyMeeting class does not support operations with {type(other)}, only other WeeklyMeetings and datetimes')
	
	# less than <
	def __lt__(self, other) -> bool:
		if type(other) is WeeklyMeeting:
			return self.day < other.day or (self.day == other.day and (self.hour < other.hour or (self.hour == other.hour and self.minute < other.minute)))
		elif type(other) is datetime.datetime:
			return self.day < other.weekday() or (self.day == other.weekday() and (self.hour < other.hour or (self.hour == other.hour and self.minute < other.minute)))
		else:
			raise TypeError(f'WeeklyMeeting class does not support operations with {type(other)}, only other WeeklyMeetings and datetimes')
	
	# less than or equal to <=
	def __le__(self, other) -> bool:
		if type(other) is WeeklyMeeting:
			return self.day < other.day or (self.day == other.day and (self.hour < other.hour or (self.hour == other.hour and self.minute <= other.minute)))
		elif type(other) is datetime.datetime:
			return self.day < other.weekday() or (self.day == other.weekday() and (self.hour < other.hour or (self.hour == other.hour and self.minute <= other.minute)))
		else:
			raise TypeError(f'WeeklyMeeting class does not support operations with {type(other)}, only other WeeklyMeetings and datetimes')
	
	# greater than >
	def __gt__(self, other) -> bool:
		if type(other) is WeeklyMeeting:
			return self.day > other.day or (self.day == other.day and (self.hour > other.hour or (self.hour == other.hour and self.minute > other.minute)))
		elif type(other) is datetime.datetime:
			return self.day > other.weekday() or (self.day == other.weekday() and (self.hour > other.hour or (self.hour == other.hour and self.minute > other.minute)))
		else:
			raise TypeError(f'WeeklyMeeting class does not support operations with {type(other)}, only other WeeklyMeetings and datetimes')
	
	# greater than or equal to >=
	def __ge__(self, other) -> bool:
		if type(other) is WeeklyMeeting:
			return self.day > other.day or (self.day == other.day and (self.hour > other.hour or (self.hour == other.hour and self.minute >= other.minute)))
		elif type(other) is datetime.datetime:
			return self.day > other.weekday() or (self.day == other.weekday() and (self.hour > other.hour or (self.hour == other.hour and self.minute >= other.minute)))
		else:
			raise TypeError(f'WeeklyMeeting class does not support operations with {type(other)}, only other WeeklyMeetings and datetimes')
	
	###########################################################################
	#
	# utility functions
	#
	###########################################################################

	# returns a datetime object of the next occurrence of this meeting
	def get_next_datetime(self) -> datetime.datetime:
		# set meeting time to today by default at the hour and minute of the meetings
		now = datetime.datetime.now(timezone)
		time = datetime.datetime(now.year, now.month, now.day, hour=self.hour, minute=self.minute, tzinfo=timezone)
		# if the meeting weekday is later in the week
		if self.day > now.weekday():
			# set the meeting time to the right day later this week
			delta = datetime.timedelta(days=(self.day - now.weekday()))
			time += delta
		# if the meeting time is earlier in the week than now
		elif self <= now:
			# set the meeting time to the right day next week
			delta = datetime.timedelta(days=(7 - now.weekday() + self.day))
			time += delta
		
		# else case is that the meeting was already set to the correct day initially
		
		return time

# class for storing bday dates and names
class BDay:
	# constructor
	def __init__(self, date: datetime.date, name: str):
		self.date = date
		self.name = name
	
	# string caster
	def __str__(self):
		# if this program is being run on windows
		if sys.platform == 'win32':
			date_str = self.date.strftime('%b %#d')
		# if this program is being run on linux, mac os, or any other os
		else:
			date_str = self.date.strftime('%b %-d')
		
		bday_str = f'{self.name}: {date_str}'
		return bday_str
	
	###########################################################################
	#
	# operator overloads
	#
	###########################################################################
	
	# equal ==
	def __eq__(self, other) -> bool:
		return self.date == other.date and self.name == other.name
	
	# not equal !=
	def __ne__(self, other) -> bool:
		return self.date != other.date or self.name != other.name
	
	# less than <
	def __lt__(self, other) -> bool:
		return self.date < other.date
	
	# less than or equal to <=
	def __le__(self, other) -> bool:
		return self.date <= other.date
	
	# greater than >
	def __gt__(self, other) -> bool:
		return self.date > other.date
	
	# greater than or equal to >=
	def __ge__(self, other) -> bool:
		return self.date >= other.date

# class for storing a server's data (like agenda order list and meeting times)
class ServerData:
	###########################################################################
	#
	# fields
	#
	###########################################################################

	# directory name of all server data
	server_root = 'server_data'
	# string format for datetimes in file saves
	dtfstr = '%Y-%m-%d %H:%M:%S %z'
	# max number of servers that the bot can be in (to save drive and ram space)
	max_servers = 100
	# max amounts of each type of data (to save drive and ram space)
	max_meetings = 100
	max_weekly_meetings = 100
	max_agenda_order = 50
	max_minutes_order = 50
	max_bdays = 50
	# file names for each type of data
	meetings_file = 'meetings.lst'
	weekly_file = 'weekly_meetings.lst'
	agenda_file = 'agenda_order.lst'
	minutes_file = 'minutes_order.lst'
	alert_file = 'alert_channel.cfg'
	bdays_file = 'bdays.lst'

	###########################################################################
	#
	# constructor
	#
	###########################################################################

	# creates a new ServerData object for a server
	# USE THIS TO CREATE SERVERDATA OBJECTS! DO NOT USE THE ACTUAL CONSTRUCTOR!
	async def create_ServerData(server):
		data = ServerData(server)
		await data.__read_all()
		return data
	
	# DO NOT USE THIS TO CONSTRUCT A SERVERDATA OBJECT! USE THE create_ServerData() FUNCTION INSTEAD!
	# THIS CONSTRUCTOR DOES NOT READ THE DATA FILES FOR ITSELF BECAUSE THE FUNCTIONS THAT DO THAT NEED TO BE ASYNC!
	def __init__(self, server):
		# initialize fields
		self.server = server
		self.meetings = []
		self.meeting_index = 0
		self.meeting_soon_loop = None
		self.meeting_now_loop = None
		self.weekly_meetings = [] # for datetime objects
		self.display_weekly_meetings = [] # for WeeklyMeeting objects
		self.weekly_meeting_index = 0
		self.weekly_meeting_soon_loop = None
		self.weekly_meeting_now_loop = None
		self.agenda_order = []
		self.agenda_index = 0
		self.minutes_order = []
		self.minutes_index = 0
		# set the meeting / bday alert channel to the first channel that the bot has message sending permissions in
		self.alert_channel = ServerData.find_first_message_channel(server)
		self.bdays = []
		self.bday_loop = None

		# create necessary folders and files if they don't already exist

		# path to server's data files
		self.folder_name = f'{ServerData.server_root}/{server.id}'
		data_files = []
		self.meetings_path = f'{self.folder_name}/{ServerData.meetings_file}'
		data_files.append(self.meetings_path)
		self.weekly_path = f'{self.folder_name}/{ServerData.weekly_file}'
		data_files.append(self.weekly_path)
		self.agenda_path = f'{self.folder_name}/{ServerData.agenda_file}'
		data_files.append(self.agenda_path)
		self.minutes_path = f'{self.folder_name}/{ServerData.minutes_file}'
		data_files.append(self.minutes_path)
		self.alert_path = f'{self.folder_name}/{ServerData.alert_file}'
		data_files.append(self.alert_path)
		self.bdays_path = f'{self.folder_name}/{ServerData.bdays_file}'
		data_files.append(self.bdays_path)

		# if the server folder doesn't exist, make one
		if not os.path.isdir(ServerData.server_root):
			os.mkdir(ServerData.server_root)
		
		# if the folder for this server's data doesn't exist, make it
		if not os.path.isdir(self.folder_name):
			os.mkdir(self.folder_name)
		
		# if any of the server's data files don't exist, make them
		for file in data_files:
			if not os.path.isfile(file):
				Path(file).touch()
	
	###########################################################################
	#
	# static functions
	#
	###########################################################################

	# returns the first text channel that the bot has permission to send messages in, returns none if there are none
	def find_first_message_channel(server):
		for channel in server.text_channels:
			channel_perms = channel.permissions_for(server.me)
			if channel_perms.send_messages:
				return channel
	
	###########################################################################
	#
	# setters
	#
	###########################################################################

	# adds a meeting time to the meeting list in sorted order with a binary search
	# returns false if the time is in the past or already in the list, true if it was successfully added
	async def add_meeting(self, time: datetime.datetime, save: bool = True) -> bool:
		# if the max list length has already been reached
		if len(self.meetings) >= ServerData.max_meetings:
			return False
		
		now = datetime.datetime.now(timezone)
		# if the meeting time is in the past
		if time < now:
			return False
		
		# insert the meeting time into a new meetings list
		l = bin_insert(self.meetings, time, no_dupes=True)
		# if the meeting time was a duplicate
		if not l:
			return False
		# if the meeting time wasn't a duplicate
		else:
			# set the meetings list to the new list
			self.meetings = l
			# get the index of the new meeting time in the list
			index = self.meetings.index(time)
			if index == self.meeting_index:
				# restart the meeting soon loop
				await self.__end_loop(self.meeting_soon_loop)
				await self.__start_meeting_soon_loop()
			elif index == 0:
				# end the meeting now loop
				await self.__end_loop(self.meeting_now_loop)
				# send a meeting soon alert and readjust the meeting index
				temp_index = self.meeting_index + 1
				self.meeting_index = index
				await self.__send_meeting_soon_alert()
				self.meeting_index = temp_index
				self.__save_meetings()
				# restart the meeting now loop
				await self.__start_meeting_now_loop()
			elif index < self.meeting_index:
				# send a meeting soon alert and readjust the meeting index
				await self.__send_meeting_soon_alert()
		
		# saves all of the meetings to the server's meetings file
		if save:
			self.__save_meetings()

		return True
	
	# adds a weekly meeting time to a weekly meeting list in sorted order with a binary search
	# returns false if the time is in the past or already in the list, true if it was successfully added
	async def add_weekly_meeting(self, time, save: bool = True) -> bool:
		# if the max list length has already been reached
		if len(self.weekly_meetings) >= ServerData.max_weekly_meetings:
			return False
		
		# if the time parameter is a WeeklyMeeting, add it to the display list first and then create a datetime object to add
		if type(time) is WeeklyMeeting:
			# insert the meeting time into a new meetings list
			l = bin_insert(self.display_weekly_meetings, time, no_dupes=True)
			# if the meeting time was a duplicate
			if not l:
				return False
			# if the meeting time wasn't a duplicate
			else:
				self.display_weekly_meetings = l
			
			# get the datetime of the next occurrence of this meeting
			next_time = time.get_next_datetime()
			# insert the meeting time into a new meetings list
			l = bin_insert(self.weekly_meetings, next_time, no_dupes=True)
			# if the meeting time was a duplicate
			if not l:
				return False
			# if the meeting time wasn't a duplicate
			else:
				self.weekly_meetings = l
		# if the time parameter is a datetime, add it to the normal list first and then create a WeeklyMeeting object to add
		elif type(time) is datetime.datetime:
			# insert the meeting time into a new meetings list
			l = bin_insert(self.weekly_meetings, time, no_dupes=True)
			# if the meeting time was a duplicate
			if not l:
				return False
			# if the meeting time wasn't a duplicate
			else:
				self.weekly_meetings = l
			
			# get a WeeklyMeeting object of this meeting time
			weekly_time = WeeklyMeeting(time.weekday(), time.hour, time.minute)
			# insert the meeting time into a new meetings list
			l = bin_insert(self.display_weekly_meetings, weekly_time, no_dupes=True)
			# if the meeting time was a duplicate
			if not l:
				return False
			# if the meeting time wasn't a duplicate
			else:
				self.display_weekly_meetings = l
		# if the time parameter isn't the right type at all
		else:
			raise TypeError('You can only add WeeklyMeeting and datetime objects with this function')
		
		# saves all of the weekly meetings to the server's weekly meetings file
		if save:
			self.__save_weekly_meetings()
		
		return True
	
	# adds a birthday to the bday list in sorted order with a binary search
	# returns true if the bday was added to the list, false if a bday on the same day for the same name is already in the list
	async def add_bday(self, bday: BDay, save: bool = True) -> bool:
		# if the max list length has already been reached
		if len(self.bdays) >= ServerData.max_bdays:
			return False

		# insert the meeting time into a new meetings list
		l = bin_insert(self.bdays, bday, no_dupes=True)
		# if the meeting time was a duplicate
		if not l:
			return False
		# if the meeting time wasn't a duplicate
		else:
			self.bdays = l
		
		# saves all of the birthdays to the server's bdays file
		if save:
			self.__save_bdays()
		
		return True
	
	# removes meetings from the server's list of meetings given a list of arguments of the meetings' numbers
	# returns true if all of the meetings were successfully removed, returns false if any of the meeting numbers wasn't valid
	async def remove_meetings(self, meeting_numbers: list, save: bool = True) -> bool:
		meeting_indexes = []
		# loop through each argument
		for arg in meeting_numbers:
			# if the argument is a positive integer
			if arg.isnumeric():
				# turn the argument into a number
				index = int(arg)
				# if the number is between 1 and the last weekly meeting number, and that index hasn't already been inputted
				if index >= 1 and index  <= len(self.meetings) and index not in meeting_indexes:
					# add that number to a list of indexes to remove
					meeting_indexes.append(index)
					continue
			
			# if any of the arguments aren't valid
			return False
		
		restart_now_loop = False
		# the soonest meeting is being removed
		if 0 in meeting_indexes:
			# end the meeting now loop and set a flag to restart it later
			await self.__end_loop(self.meeting_now_loop)
			restart_now_loop = True
		
		restart_soon_loop = False
		# if the meeting at the meeting index is being removed
		if self.meeting_index in meeting_indexes:
			# end the meeting soon loop and set a flag to restart it later
			await self.__end_loop(self.meeting_soon_loop)
			restart_soon_loop = True
		
		# sort the list of indexes in reverse order because the right indexes will change while they're being removed if they're iterated through ascending order
		meeting_indexes.sort(reverse=True)
		# remove each meeting from the list in reverse order
		for i in meeting_indexes:
			# calculate the actual index
			index = i - 1
			# remove the meeting from the list
			self.meetings = self.meetings[:index] + self.meetings[i:]
			# if the index of the meeting is less than the meeting index, decrement the meeting index
			if index < self.meeting_index:
				self.adjust_meeting_index(-1)
		
		# if the meeting now loop was stopped, restart it
		if restart_now_loop:
			await self.__start_meeting_now_loop()
		
		# if the meeting soon loop was stopped, restart it
		if restart_soon_loop:
			await self.__start_meeting_soon_loop()
		
		# saves all of the remaining meetings to the server's meetings file
		if save:
			self.__save_meetings()

		return True
	
	# removes weekly meetings from the server's lists of weekly meetings given a list of arguments of the meetings' numbers
	# returns true if all of the meetings were successfully removed, returns false if any of the meeting numbers wasn't valid
	def remove_weekly_meetings(self, meeting_numbers: list, save: bool = True) -> bool:
		meeting_indexes = []
		# loop through each argument
		for arg in meeting_numbers:
			# if the argument is a positive integer
			if arg.isnumeric():
				# turn the argument into a number
				index = int(arg)
				# if the number is between 1 and the last weekly meeting number, and that index hasn't already been inputted
				if index >= 1 and index  <= len(self.display_weekly_meetings) and index not in meeting_indexes:
					# add that number to a list of indexes to remove
					meeting_indexes.append(index)
					continue
			
			# if any of the arguments aren't valid
			return False
		
		# sort the list of indexes in reverse order because the right indexes will change while they're being removed if they're iterated through ascending order
		meeting_indexes.sort(reverse=True)
		# remove each meeting from both lists in reverse order
		for i in meeting_indexes:
			# calculate the actual index
			index = i - 1
			try:
				# find the index of the corresponding datetime object to this WeeklyMeeting object in the other list
				other_index = self.weekly_meetings.index(self.display_weekly_meetings[index])
				# remove the datetime object from its list
				self.weekly_meetings = self.weekly_meetings[:other_index] + self.weekly_meetings[other_index+1:]
				# if the index of the datetime is less than the weekly meeting index and, decrement the weekly meeting index
				if other_index < self.weekly_meeting_index:
					self.adjust_weekly_meeting_index(-1)
			except:
				# just ignore it if it can't find the corresponding object since it's already not there lol
				pass
			# pop the WeeklyMeeting object from its list
			self.display_weekly_meetings = self.display_weekly_meetings[:index] + self.display_weekly_meetings[i:]
		
		# saves all of the remaining meetings to the server's meetings file
		if save:
			self.__save_weekly_meetings()
		
		return True
	
	# adds i to the meeting index (default -1) and keeps the index within range
	def adjust_meeting_index(self, i: int = -1, save: bool = True):
		self.meeting_index += i
		# if the meeting index went below 0, set it back to 0
		if self.meeting_index < 0:
			self.meeting_index = 0
		# if the meeting index went above the length of the meeting list, set it back to the length of the meeting list
		elif self.meeting_index > len(self.meetings):
			self.meeting_index = len(self.meetings)
		
		# saves the meeting data
		if save:
			self.__save_meetings()
	
	# adds i to the weekly meeting index (default -1) and keeps the index within range
	def adjust_weekly_meeting_index(self, i: int = -1, save: bool = True):
		self.weekly_meeting_index += i
		# if the weekly meeting index went below 0, set it back to 0
		if self.weekly_meeting_index < 0:
			self.weekly_meeting_index = 0
		# if the weekly meeting index went above the length of the weekly meeting list, set it back to the length of the weekly meeting list
		elif self.weekly_meeting_index > len(self.weekly_meetings):
			self.weekly_meeting_index = len(self.weekly_meetings)
		
		# saves the weekly meeting data
		if save:
			self.__save_weekly_meetings()
	
	# removes a birthday from the server's list of birthdays given a bday object
	# returns true if the bday was found and removed, false if it wasn't
	def remove_bday(self, bday: BDay, save: bool = True) -> bool:
		# if the bday is in the list
		if bday in self.bdays:
			# remove it from the list and return true
			index = self.bdays.index(bday)
			self.bdays.pop(index)
			# saves all of the birthdays to the server's bdays file
			if save:
				self.__save_bdays()
			
			return True
		# if the bday is not in the list
		else:
			return False
	
	# sets the agenda notetaking order to a given list of names
	def set_agenda_order(self, names: list, save: bool = True) -> bool:
		# if the names list is longer than the max allowed length
		if len(names) >= ServerData.max_agenda_order:
			return False
		
		# set the list and reset the index
		self.agenda_order = names
		self.agenda_index = 0

		# saves the agenda order and index to the server folder
		if save:
			self.__save_agenda()

		return True
	
	# sets the meeting minutes notetaking order to a given list of names
	def set_minutes_order(self, names: list, save: bool = True) -> bool:
		# if the names list is longer than the max allowed length
		if len(names) >= ServerData.max_minutes_order:
			return False
		
		# set the list and reset the index
		self.minutes_order = names
		self.minutes_index = 0

		# saves the meeting minutes order and index to the server folder
		if save:
			self.__save_minutes()

		return True
	
	# sets the agenda index to the inputted name at that index
	# returns true if the name was found, false if it wasn't
	def set_agenda_to(self, name: str, save: bool = True) -> bool:
		# if the name is in the list
		if name in self.agenda_order:
			# set the index to that name's index
			self.agenda_index = self.agenda_order.index(name)
			# saves the agenda order and index to the server folder
			if save:
				self.__save_agenda()
			
			return True
		else:
			return False
	
	# sets the minutes index to the inputted name at that index
	# returns true if the name was found, false if it wasn't
	def set_minutes_to(self, name: str, save: bool = True) -> bool:
		# if the name is in the list
		if name in self.minutes_order:
			# set the index to that name's index
			self.minutes_index = self.minutes_order.index(name)
			# saves the meeting minutes order and index to the server folder
			if save:
				self.__save_minutes()
			
			return True
		else:
			return False
	
	# sets the agenda duty list to an empty list and the agenda index to 0
	def clear_agenda_order(self, save: bool = True):
		# clear the list and reset the index
		self.agenda_order = []
		self.agenda_index = 0

		# saves the agenda order and index to the server folder
		if save:
			self.__save_agenda()
	
	# sets the meeting minutes duty list to an empty list and the minutes index to 0
	def clear_minutes_order(self, save: bool = True):
		# clear the list an reset the index
		self.minutes_order = []
		self.minutes_index = 0

		# saves the meeting minutes order and index to the server folder
		if save:
			self.__save_minutes()
	
	# increases the agenda order index by i (default 1), loops back to the start if it's at the end
	def inc_agenda(self, i: int = 1, save: bool = True):
		# if there is an agenda list
		if len(self.agenda_order) > 0:
			self.agenda_index = (self.agenda_index + i) % len(self.agenda_order)

			# saves the agenda data
			if save:
				self.__save_agenda()
	
	# increases the meeting minutes order index by i (default 1), loops back to the start if it's at the end
	def inc_minutes(self, i: int = 1, save: bool = True):
		# if there is a meeting minutes list
		if len(self.minutes_order) > 0:
			self.minutes_index = (self.minutes_index + i) % len(self.minutes_order)

			# saves the meeting minutes data
			if save:
				self.__save_minutes()
	
	# sets the alert channel for a server to the one that is inputted
	# returns false if it can't be set to that channel, true if it was successfully set to it
	def set_alert_channel(self, channel):
		# if the channel is not in the same server as the this object's server
		if channel.guild != self.server:
			raise ValueError('Server passed as argument not the same as the object\'s server')
		
		# if the channel is the same as the current alert channel
		if channel == self.alert_channel:
			return True
		
		channel_perms = channel.permissions_for(channel.guild.me)
		# if the bot has permission to send messages in this channel
		if channel_perms.send_messages:
			# set this server's alert channel to this channel and return true
			self.alert_channel = channel
			# save the new alert channel
			self.__save_alert_channel()
			return True
		# if the bot doesn't have permission to send messages in this channel
		else:
			return False
	
	# sets the alert channel for this server to the first text channel that the bot can send messages in
	# sets it to none if the bot doesn't have permission to send messages in any of the channels
	def reset_alert_channel(self, server):
		# if the server is not the same as this object's server
		if server != self.server:
			raise ValueError('Server passed as argument not the same as the object\'s server')
		
		# get the first channel in this server that the bot has permission to send messages in
		channel = ServerData.find_first_message_channel(server)
		# if the new alert channel is different than the old one
		if channel != self.alert_channel:
			# set the alert channel to the new one and save it
			self.alert_channel = channel
			self.__save_alert_channel()
	
	###########################################################################
	#
	# data backup / saving functions
	#
	###########################################################################

	# saves the meetings list to the server's meetings file
	def __save_meetings(self):
		file_lines = ''
		# combine every item in the list into a newline separated string
		for meeting in self.meetings:
			file_lines += meeting.strftime(ServerData.dtfstr + '\n')
		
		# write the meeting index and the datetimes to the meetings file
		with open(self.meetings_path, 'w') as file:
			file.write(f'{self.meeting_index}\n')
			file.write(file_lines)
	
	# saves the weekly meetings list to the server's weekly meetings file
	# note: only saves the datetime objects so the bot can know how many meetings it missed so it can set the agenda
	# and minutes indexes properly
	def __save_weekly_meetings(self):
		file_lines = ''
		# combine every item in the list into a newline separated string
		for meeting in self.weekly_meetings:
			file_lines += meeting.strftime(ServerData.dtfstr + '\n')
		
		# write the meeting index and the datetimes to the meetings file
		with open(self.weekly_path, 'w') as file:
			file.write(f'{self.weekly_meeting_index}\n')
			file.write(file_lines)
	
	# saves the agenda order list and index to the server's agenda order file
	def __save_agenda(self):
		file_lines = ''
		# combine every item in the list into a newline separated string
		for name in self.agenda_order:
			file_lines += name + '\n'
		
		# write the index and the items to the data file
		with open(self.agenda_path, 'w', encoding='utf8') as file:
			file.write(f'{self.agenda_index}\n')
			file.write(file_lines)
	
	# saves the meeting minutes order list and index to the server's minutes order file
	def __save_minutes(self):
		file_lines = ''
		# combine every item in the list into a newline separated string
		for name in self.minutes_order:
			file_lines += name + '\n'
		
		# write the index and the items to the data file
		with open(self.minutes_path, 'w', encoding='utf8') as file:
			file.write(f'{self.minutes_index}\n')
			file.write(file_lines)
	
	# saves the alert channel to the server's alert channel file
	def __save_alert_channel(self):
		with open(self.alert_path, 'w') as file:
			# if this server has an alert channel, write its id to the file
			if self.alert_channel is not None:
				file.write(f'{self.alert_channel.id}\n')
			# if this server doesn't have an alert channel, write an empty string to the file
			else:
				file.write('')
	
	# saves the birthdays list to the server's bdays file
	def __save_bdays(self):
		file_lines = ''
		# combine every item in the list into a newline separated string
		for bday in self.bdays:
			date_str = bday.date.strftime(ServerData.dtfstr)
			file_lines += f'{bday.name} {date_str}\n'
		
		# write the dates to the meetings file
		with open(self.bdays_path, 'w') as file:
			file.write(file_lines)
	
	###########################################################################
	#
	# data reading functions
	#
	###########################################################################

	# reads all of the data files, stores them in this object, and updates the files if needed
	async def __read_all(self):
		# do agenda and minutes first since reading the meetings data can change the agenda and minutes data
		# read saved agenda data
		self.__read_agenda()
		# read saved minutes data
		self.__read_minutes()
		# read saved meeting data
		await self.__read_meetings()
		# weekly meeting data
		await self.__read_weekly_meetings()
		# alert channel data
		self.__read_alert_channel()
		# read saved bday data
		await self.__read_bdays()

	# reads data from the meetings file, stores it in this object, and updates the file if needed
	async def __read_meetings(self):
		# flag if the list was updated while reading it
		update = False
		
		# read the meetings file
		with open(self.meetings_path, 'r') as file:
			lines = file.readlines()
		
		# if the file was empty
		if len(lines) <= 0:
			self.__save_meetings()
		# if the file wasn't empty
		else:
			index = lines[0].strip()
			# if the first line is a positive integer
			if index.isnumeric():
				# set the meeting index to the number on the first line
				self.meeting_index = int(index)
			# else let it stay as 0
			
			# get the current date and time
			now = datetime.datetime.now(timezone)
			# for each line that was read in the file
			for line in lines[1:]:
				# get the date and time of the meeting from the string
				try:
					meeting = datetime.datetime.strptime(line.strip(), ServerData.dtfstr)
				# just do the next line if this one is wrong
				except:
					continue

				# if the meeting time is in the future, add it to the server's meetings list
				if meeting > now:
					await self.add_meeting(meeting, save=False)
				# if the meeting already happened, don't add it to the list and increment the minutes index
				else:
					# set the update flag to true so the bot will update the data in the file
					update = True
					# set the minutes to the next person and decrease the index
					self.inc_minutes()
					self.adjust_meeting_index(-1, save=False)
			
			# if there were any changes to the list while reading it, save the new list
			if update:
				self.__save_meetings()
	
	# reads data from the weekly meetings file, stores it in this object, and updates the file if needed
	async def __read_weekly_meetings(self):
		# flag if the list was updated while reading it
		update = False

		# read the weekly meetings file
		with open(self.weekly_path, 'r') as file:
			lines = file.readlines()
		
		# if the file was empty
		if len(lines) <= 0:
			self.__save_weekly_meetings()
		# if the file wasn't empty
		else:
			index = lines[0].strip()
			# if the first line is a positive integer
			if index.isnumeric():
				# set the meeting index to the number on the first line
				self.weekly_meeting_index = int(index)
			# else let it stay as 0
			
			# get the current date and time
			now = datetime.datetime.now(timezone)
			# for each line that was read in the file
			for line in lines[1:]:
				# get the date and time of the meeting from the string
				try:
					meeting = datetime.datetime.strptime(line.strip(), ServerData.dtfstr)
				# just do the next line if this one is wrong
				except:
					continue

				# if the meeting time is in the past
				if meeting < now:
					# set the update flag to true so the bot will update the data in the file
					update = True
					# calculate how much time has passed since this meeting
					delta = now - meeting
					# calculate how many of these weekly meetings were missed
					meetings_missed = delta.days // 7
					delta_week_mod = delta.days % 7
					# if today is the same weekday day as this weekly meeting
					if delta_week_mod == 0:
						today_meeting = meeting + delta
						# if the meeting has already happened today
						if today_meeting < now:
							# make it so this weekly meeting will be stored as next week
							delta_week_mod = 14
						# if it hasn't happened yet today
						else:
							# don't include this meeting as being missed
							meetings_missed -= 1
					
					# calculate how many days to add to the meeting to put it to the next weekly occurrence
					delta = datetime.timedelta(days = delta.days + (7 - delta_week_mod))
					print(delta.days % 7)
					# add the days to the meeting time
					meeting += delta
					# increase the agenda and meeting minutes indexes for how many meetings were missed and decrease the meetings index
					self.inc_agenda(meetings_missed)
					self.inc_minutes(meetings_missed)
					self.adjust_weekly_meeting_index(-1, save=False)
				
				# add the meeting to the weekly meetings list
				await self.add_weekly_meeting(meeting, save=False)
			
			# if there were any changes to the list while reading it, save the new list
			if update:
				self.__save_weekly_meetings()
	
	# reads data from the agenda order file, stores it in this object, and updates the file if needed
	def __read_agenda(self):
		# read the agenda order file
		with open(self.agenda_path, 'r', encoding='utf8') as file:
			lines = file.readlines()
		
		# remove the newline from each name and add it to the agenda order list
		for line in lines[1:]:
			self.agenda_order.append(line.strip())
		
		# if the file was empty
		if len(lines) <= 0:
			self.__save_agenda()
		else:
			# remove newline from index
			index = lines[0].strip()
			# if the index is a positive integer
			if index.isnumeric():
				# grab the index
				self.agenda_index = int(index)
				# if the index is too big
				if self.agenda_index >= len(self.agenda_order):
					# set the index to 0 and update the data in the list's file
					self.agenda_index = 0
					self.__save_agenda()
			# if the index is not a positive integer, update the data in the list's file so the index in there will be 0
			else:
				self.__save_agenda()
	
	# reads data from the meeting minutes order file, stores it in this object, and updates the file if needed
	def __read_minutes(self):
		# read the meeting minutes order file
		with open(self.minutes_path, 'r', encoding='utf8') as file:
			lines = file.readlines()
		
		# remove the newline from each name and add it to the meeting minutes order list
		for line in lines[1:]:
			self.minutes_order.append(line.strip())
		
		# if the file was empty
		if len(lines) <= 0:
			self.__save_agenda()
		else:
			# remove newline from index
			index = lines[0].strip()
			# if the index is a positive integer
			if index.isnumeric():
				# grab the index
				self.minutes_index = int(index)
				# if the index is too big
				if self.minutes_index >= len(self.minutes_order):
					# set the index to 0 and update the data in the list's file
					self.minutes_index = 0
					self.__save_minutes()
			# if the index is not a positive integer, update the data in the list's file so the index in there will be 0
			else:
				self.__save_minutes()
	
	# reads data from the alert_channel file, stores it in this object, and updates the file if needed
	def __read_alert_channel(self):
		# read the alert channel
		with open(self.alert_path, 'r') as file:
			channel_id = file.read().strip()
			# try converting the data read from the file into a discord channel object
			try:
				self.alert_channel = client.get_channel(int(channel_id))
			# if the file didn't have a valid discord channel id in it
			except:
				# reset the alert channel
				self.reset_alert_channel(self.server)
				return
		
		# if the text channel exists in this server
		if self.alert_channel in self.server.text_channels:
			channel_perms = self.alert_channel.permissions_for(self.server.me)
			# if the bot doesn't have permission to send messages in this channel
			if not channel_perms.send_messages:
				# reset the alert channel
				self.reset_alert_channel(self.server)
		# if the text channel doesn't exist in this server
		else:
			# reset the alert channel
			self.reset_alert_channel(self.server)
	
	# reads data from th birthdays file, stores it in this object, and updates the file if needed
	async def __read_bdays(self):
		# flag if the list was updated while reading it
		update = False

		# read the bdays file
		with open(self.bdays_path, 'r') as file:
			lines = file.readlines()
		
		# get the current date and time
		now = datetime.datetime.now(timezone)
		# for each line that was read in the file
		for line in lines:
			# get the name and datetime of the bday
			try:
				# assume the name of the bday goes up to the 20th last character, which is where the datetime should begin (including the newline char)
				index = -26
				name = line[:index].strip()
				# get the datetime of the bday
				date = datetime.datetime.strptime(line[index:].strip(), ServerData.dtfstr)
			# set the update flag and do the next line if this one is wrong
			except:
				update = True
				continue

			# if the bday is in the past, update the year so it can be put back into the list
			if date < now:
				# set the update flag to true so the bot will update the data in the file
				update = True
				date.year = now.year
				# if the bday is still in the past when is has the same year as now, set it's year to next year
				if date < now:
					date.year += 1
			
			# construct the bday object and add it to the list in order
			bday = BDay(date, name)
			await self.add_bday(bday, save=False)
		
		# if there were any changes to the list while reading it, save the new list
		if update:
			self.__save_bdays()
	
	###########################################################################
	#
	# alert functions
	#
	###########################################################################

	# @s everyone to say that a meeting will be soon, what time it will be at, and who's on meeting minutes duty for it
	# also adjusts the meeting index to put the next meeting on deck for being alerted about, and starts a meeting now loop if there isn't already one
	async def __send_meeting_soon_alert(self):
		# if this program is being run on windows
		if sys.platform == 'win32':
			message = self.meetings[self.meeting_index].strftime(f'@everyone **Meeting Soon at %#H:%M / %#I:%M %p {tzstr}**\n\n')
		# if this program is being run on linux, mac os, or any other os
		else:
			message = self.meetings[self.meeting_index].strftime(f'@everyone **Meeting Soon at %-H:%M / %-I:%M %p {tzstr}**\n\n')
		
		# if there is a meeting minutes list
		if len(self.minutes_order) > 0:
			message += f'**Meeting Minutes Duty:** {self.minutes_order[self.minutes_index]}'
		# if none of the message was sent
		if not await safe_message(self.alert_channel, message):
			# try finding a new alert channel and sending it there
			self.reset_alert_channel(self.server)
			safe_message(self.alert_channel, message)
		
		# increase the meeting index so the next meeting gets checked for
		self.adjust_meeting_index(1)
		# start a meeting now loop if there isn't already one running
		await self.__start_meeting_now_loop()
	
	# @s everyone to say that a weekly meeting will be soon, what time it will be at, and who's on meeting minutes duty for it
	# also adjusts the weekly meeting index to put the next weekly meeting on deck for being alerted about, and starts a weekly meeting now loop if there isn't already one
	async def __send_weekly_meeting_soon_alert():
		pass

	# @s everyone to say that a meeting has started and who's on meeting minutes duty for it
	# also removes the first meeting from the meetings list and adjusts indexes adjust to the next meeting
	async def __send_meeting_now_alert(self):
		# constructs the message
		message = '@everyone **Meeting Now**\n\n'
		# if there is a meeting minutes list
		if len(self.minutes_order) > 0:
			message += f'**Meeting Minutes Duty:** {self.minutes_order[self.minutes_index]}'
		
		# if none of the message was sent
		if not await safe_message(self.alert_channel, message):
			# try finding a new alert channel and sending it there
			self.reset_alert_channel(self.server)
			safe_message(self.alert_channel, message)
		
		# remove the first meeting from the list
		self.meetings = self.meetings[1:]
		# go to the next person on meeting minutes duty
		self.inc_minutes()
		# decrease the meeting index to account for the pop
		self.adjust_meeting_index(-1)
	
	# @s everyone to say that a weekly meeting has started and who's on meeting minutes duty for it
	# also moves the first meeting in the weekly meeting list to the back of the list by adjusting it to be 1 week later
	async def __send_weekly_meeting_now_alert():
		pass

	# @s everyone to say happy birthday to someone and moves that birthday to the back of the list by adjusting it to be 1 year later
	async def __send_bday_alert():
		pass
	
	###########################################################################
	#
	# loop control functions
	#
	###########################################################################

	# creates a new async task for the meeting soon loop if there isn't already one currently running
	async def __start_meeting_soon_loop(self):
		if self.meeting_soon_loop is None or self.meeting_soon_loop.cancelled() or self.meeting_soon_loop.done():
			self.meeting_soon_loop = client.loop.create_task(self.__meeting_soon_loop())

	# creates a new async task for the weekly meeting soon loop if there isn't already one currently running
	async def __start_weekly_meeting_soon_loop(self):
		if self.weekly_meeting_soon_loop is None or self.weekly_meeting_soon_loop.cancelled() or self.weekly_meeting_soon_loop.done():
			self.weekly_meeting_soon_loop = client.loop.create_task(self.__weekly_meeting_soon_loop())

	# creates a new async task for the meeting now loop if there isn't already one currently running
	async def __start_meeting_now_loop(self):
		if self.meeting_now_loop is None or self.meeting_now_loop.cancelled() or self.meeting_now_loop.done():
			self.meeting_now_loop = client.loop.create_task(self.__meeting_now_loop())
	
	# creates a new async task for the weekly meeting now loop if there isn't already one currently running
	async def __start_weekly_meeting_now_loop(self):
		if self.weekly_meeting_now_loop is None or self.weekly_meeting_now_loop.cancelled() or self.weekly_meeting_now_loop.done():
			self.weekly_meeting_now_loop = client.loop.create_task(self.__weekly_meeting_now_loop())

	# creates a new async task that says happy birthday on peoples' birthdays
	async def __start_bday_loop(self):
		if self.bday_loop is None or self.bday_loop.cancelled() or self.bday_loop.done():
			self.bday_loop = client.loop.create_task(self.__bday_loop())

	# stops an async task from running if it currently is running
	async def __end_loop(self, loop):
		if loop is not None and not loop.cancelled() and not loop.done():
			loop.cancel()

	###########################################################################
	#
	# time check loop functions
	#
	###########################################################################

	# gives warnings when a meeting is in 30 minutes
	async def __meeting_soon_loop(self):
		delta_30min = datetime.timedelta(minutes = 30)
		# while there are meetings left in the list to check for
		while self.meeting_index < len(self.meetings):
			# get the current time
			now = datetime.datetime.now(timezone)
			# get the time of 30 minutes before the index meeting
			alert_time = self.meetings[self.meeting_index] - delta_30min
			# calculate how many seconds to wait from now until 30 minutes before the index meeting
			wait_time = (alert_time - now).total_seconds()
			# if the meeting is more than 30 minutes away from now
			if wait_time > 0:
				# wait until 30 minutes before the index meeting
				await asyncio.sleep(wait_time)
			# send an alert about the meeting being soon
			await self.__send_meeting_soon_alert()
	
	# gives warnings when a weekly meeting is in 30 minutes
	async def __weekly_meeting_soon_loop(self):
		pass
	
	# gives alerts when a meeting is starting
	async def __meeting_now_loop(self):
		# while there are still meetings in the list that have already had a soon alert go out
		while len(self.meetings[:self.meeting_index]) > 0:
			# get the current time
			now = datetime.datetime.now(timezone)
			# calculate how many seconds to wait from now until the next meeting
			wait_time = (self.meetings[0] - now).total_seconds()
			# if the next meeting hasn't started yet
			if wait_time > 0:
				# wait until the meeting starts
				await asyncio.sleep(wait_time)
			# send an alert about the meeting starting
			await self.__send_meeting_now_alert()
	
	# gives alerts when a weekly meeting is starting
	async def __weekly_meeting_now_loop(self):
		pass
	
	# gives alerts at 8:00 am when it's someone's bday
	async def __bday_loop(self):
		pass

########################################################################################################################
#
# startup instructions
#
########################################################################################################################

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
		server_data[server] = await ServerData.create_ServerData(server)
	
	# prints message that the bot is done setting up
	print(datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), f"{sys.argv[0]}:", "Bot is running")

# sets up the bot for a new server every time it joins one while running
@client.event
async def on_guild_join(server):
	if len(server_data) <= 100:
		server_data[server] = await ServerData.create_ServerData(server)
	else:
		channel = ServerData.find_first_message_channel(server)
		if channel is not None:
			message = f'I am already in my maximum amount of servers ({ServerData.max_servers}). '
			if contact_info != '':
				message += f'Contact my admin if you wish to reserve a spot for your server with the me ({contact_info}). '
				message += 'You can also visit the repository for my code for more info(https://github.com/ChandlerJayCalkins/Capstone-Meeting-Bot). '
			message += 'Leaving server...'
			channel.send(message)
		await server.leave()

########################################################################################################################
#
# discord event updates
#
########################################################################################################################

# removes all of a server's data when the bot leaves a server
@client.event
async def on_guild_remove(server):
	# TODO: make it so the bot hangs onto a server's data for a day before it deletes it
	# if the server's data exists
	if server in server_data:
		# deletes the folder and all files in it if the folder exists
		if os.path.isdir(server_data[server].server_folder):
			shutil.rmtree(server_data[server].server_folder)
		
		# deletes the server's data from ram
		server_data.pop(server)

# finds a new alert channel for a server if the current alert channel for a server was deleted
@client.event
async def on_guild_channel_delete(channel):
	# update the server object that is being stored in memory
	server_data[channel.guild].server = channel.guild
	# if the channel that was deleted is the server's alert channel
	if server_data[channel.guild].alert_channel == channel:
		# set the alert channel to the first text channel that the bot can send messages in
		server_data[channel.guild].reset_alert_channel(channel.guild)

# finds a new alert channel for a server if the current alert channel doesn't give the bot permission to send messages anymore
@client.event
async def on_guild_channel_update(before, after):
	# update the server object that is being stored in memory
	server_data[before.guild].server = after.guild
	# if the channel that was updated is the server's alert channel
	if server_data[before.guild].alert_channel == before:
		channel_perms = server_data[before.guild].alert_channel.permissions_for(after.guild.me)
		# if the bot doesn't have permission to send messages in the alert channel anymore
		if not channel_perms.send_messages:
			# set the alert channel to the first text channel that the bot can send messages in
			server_data[before.guild].reset_alert_channel(after.guild)

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
	# if the message is a command from a valid source, it starts with a command prefix, and the bot has the data for this server set up
	if await is_command(message) and message.guild in server_data:
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
			reply = f'`{command}:` Gives info about the me and my commands!\n\n'

			reply += '```Usages:```\n'

			reply += f'**{desktop_prefix} help**\n'
			reply += 'This will print out the default help message that shows how to use me and lists all of my commands.\n\n'

			reply += f'**{desktop_prefix} help [command]**\n'
			reply += 'Gives info on [command].\n'

			reply += '\n```Examples:```\n'

			reply += f'{desktop_prefix} help\n'
			reply += f'{desktop_prefix} help add\n'
			reply += f'{desktop_prefix} help meetings'

			await safe_reply(message, reply)
		# if the info on the add command was requested
		elif command == 'add':
			# list of string lines that the bot will reply to the help command with
			reply = f'`{command}:` Adds a meeting or a birthday for me to keep track of so I can remind you about it.\n\n'

			reply += '```Usages:```\n'

			reply += f'**{desktop_prefix} add meeting on [date] at [time]**\n'
			reply += 'This will add a meeting to keep track of and I will remind you about the meeting on [date] a few minutes before [time] and then forget about it.\n'
			reply += 'Note: you cannot add a meeting with the exact same time and date as an already existing meeting.\n\n'

			reply += f'**{desktop_prefix} add weekly meeting on [day] at [time]**\n'
			reply += 'This will add a meeting to to keep track of that recurs every week and I will remind you about the meeting every week on [day] a few minutes before [time].\n'
			reply += 'Note: you cannot add a weekly meeting with the exact same time and day as an already existing weekly meeting.\n\n'

			reply += f'**{desktop_prefix} add bday on [date] for [name]**\n'
			reply += 'This will add a birthday to keep track of and I will say happy birthday on [date] to [name].\n'
			reply += 'Note: you cannot add a birthday for a person with the exact same name and date as an already existing birthday.\n\n'

			reply += '**Formatting:**\n\n'
			reply += '**[date]:** YYYY/M/D or YYYY-M-D M/D or M-D (YYYY = year (1 <= YYYY <= 9999), M = month (1 <= M <= 12), D = day (1 <= D <= 31)).\n'
			reply += 'Note: if the year is not inputted in the date, the next available date on M/D will be inputted. I will ignore years on bday inputs.\n'
			reply += '**[time]:** H:M or H:M am/pm or H or H am/pm (H = hour (1 <= H <= 12 or 1 <= H <= 24), M = minute (1 <= M <= 59)).\n'
			reply += '**[day]:** Sundays: (su, sun, sunday, sundays), Mondays: (m, mon, monday, mondays), Tuesdays: (tu, tue, tues, tuesday, tuesdays), '
			reply += 'Wednesdays: (w, wed, wednesday, wednesdays), Thursdays: (th, thu, thur, thurs, thursday, thursdays), Fridays: (f, fri, friday, fridays), '
			reply += 'Saturdays: (sa, sat, saturdays, saturdays).\n\n'

			reply += '```Examples:```\n'

			reply += f'{desktop_prefix} add meeting on 11/15 at 10:30 am\n'
			reply += f'{desktop_prefix} add weekly meeting on tu at 15:30\n'
			reply += f'{desktop_prefix} add bday on 1/7 for Chandler\n'
			reply += f'{desktop_prefix} add meeting on 9-20 at 4 pm\n'
			reply += f'{desktop_prefix} add weekly meeting on mondays at 18\n'
			reply += f'{desktop_prefix} add bday on 12-1 for Josh\n'
			reply += f'{desktop_prefix} add meeting on 2024/10/31 at 1 am\n'
			reply += f'{desktop_prefix} add weekly meeting on friday at 1:45 pm\n'
			reply += f'{desktop_prefix} add bday on 4/1 for Francis Fulloffrenchpeople'

			await safe_reply(message, reply)
		# if the info on the remove command was requested
		elif command == 'remove':
			# list of string lines that the bot will reply to the help command with
			reply = f'`{command}:` Removes a meeting, a birthday, or clear the agenda or meeting minutes duty list from my memory.\n\n'

			reply += '```Usages:```\n'

			reply += f'**{desktop_prefix} remove meeting [meeting number(s)]**\n'
			reply += 'This will remove the meeting(s) with the numbers [meeting number(s)].\n'
			reply += 'Note: You can find a meeting\'s number with the "meetings" command (it\'s the number to the left of the meeting).\n\n'

			reply += f'**{desktop_prefix} remove meetings [meeting number(s)]**\n'
			reply += 'Same as above.\n\n'

			reply += f'**{desktop_prefix} remove weekly meeting [meeting number(s)]**\n'
			reply += 'This will remove the weekly meeting(s) with the numbers [meeting number(s)].\n'
			reply += 'Note: You can find a meeting\'s number with the "meetings" command (it\'s the number to the left of the meeting).\n\n'

			reply += f'**{desktop_prefix} remove weekly meetings [meeting number(s)]**\n'
			reply += 'Same as above.\n\n'

			reply += f'**{desktop_prefix} remove agenda**\n'
			reply += 'Clears the agenda notetaking duty list.\n\n'

			reply += f'**{desktop_prefix} remove minutes**\n'
			reply += 'Clears the meeting minutes notetaking duty list.\n\n'

			reply += f'**{desktop_prefix} remove bday on [date] for [name]**\n'
			reply += 'This will remove a birthday on [date] for the person named [name].\n'
			reply += 'Note: You can see which birthdays have been added with the "bdays" command.\n\n'

			reply += '**Formatting:**\n\n'
			reply += '**[date]:** M/D or M-D (M = month (1 <= M <= 12), D = day (1 <= D <= 31)).\n\n'

			reply += '```Examples:```\n'

			reply += f'{desktop_prefix} remove meeting 1\n'
			reply += f'{desktop_prefix} remove weekly meeting 2 6 4\n'
			reply += f'{desktop_prefix} remove agenda\n'
			reply += f'{desktop_prefix} remove bday on 1/7 for Chandler\n'
			reply += f'{desktop_prefix} remove meetings 7 3 5\n'
			reply += f'{desktop_prefix} remove weekly meetings 8\n'
			reply += f'{desktop_prefix} remove minutes\n'
			reply += f'{desktop_prefix} remove bday on 12-1 for Josh\n'

			await safe_reply(message, reply)
		# if the info on the meetings command was requested
		elif command == 'meetings':
			# list of string lines that bot will reply to the help command with
			reply = f'`{command};` Displays all meetings and weekly meetings.\n\n'

			reply += '```Usage:```\n'

			reply += f'**{desktop_prefix} meetings**\n'
			reply += 'This will display all meetings and weekly meetings that I am currently keeping track of along with each meeting\'s removal number.\n'
			reply += 'Note: See how to use the meeting removal numbers and remove meetings in the "remove" command info, as well as how to add '
			reply += 'meetings in the "add" command info.'

			await safe_reply(message, reply)
		# if the info on the set command was requested
		elif command == 'set':
			# list of string lines that the bot will reply to the help command with
			reply = f'`{command}:` Sets the agenda or meeting minutes notetaking order.\n\n'

			reply += '```Usages:```\n'

			reply += f'**{desktop_prefix} set agenda order as [name], [name], [name], ...**\n'
			reply += 'This will set the agenda notetaking order as the list of names at the end of the command.\n'
			reply += 'I will also reset the agenda notetaking list to start at the first name in this command and work my way down.\n'
			reply += 'Every time there is a meeting I will remind you whose turn it is on agenda, and after the meeting has started '
			reply += 'I will move onto the next person in the list for the next meeting.\n'
			reply += 'Note: See the current agenda order in the "dutyorder" command info.\n\n'

			reply += f'**{desktop_prefix} set minutes order as [name], [name], [name], ...**\n'
			reply += 'This will set the meeting minutes notetaking order as the list of names at the end of the command.\n'
			reply += 'I will also reset the meeting minutes notetaking list to start at the first name in this command and work my way down.\n'
			reply += 'Every time there is a meeting, I will remind you whose turn it is on minutes, and after the meeting has started '
			reply += 'I will move onto the next person in the list for the next meeting.\n'
			reply += 'Note: See the current meeting minutes order in the "dutyorder" command info.\n\n'

			reply += f'**{desktop_prefix} set agenda to [name]**\n'
			reply += 'This will set the next person from the agenda list on agenda notetaking duty to [name].\n'
			reply += 'Note: See the current agenda order in the "dutyorder" command info.\n\n'

			reply += f'**{desktop_prefix} set minutes to [name]**\n'
			reply += 'This will set the next person from the minutes list on meeting minutes notetaking duty to [name].\n'
			reply += 'Note: See the current meeting minutes order in the "dutyorder" command info.\n\n'

			reply += '**Formatting:**\n\n'
			reply += 'Multiple names must be separated by commas.\n'

			reply += '```Examples:```\n'

			reply += f'{desktop_prefix} set agenda order as Chandler Glen Holly\n'
			reply += f'{desktop_prefix} set minutes order as Grant David Tyler\n'
			reply += f'{desktop_prefix} set agenda to Glen\n'
			reply += f'{desktop_prefix} set minutes to Tyler\n'

			await safe_reply(message, reply)
		# if the info on the dutyorder command was requested
		elif command == 'dutyorder':
			# list of string lines that the bot will reply to the help command with
			reply = f'`{command}:` Displays the current agenda and meeting minutes notetaking order.\n\n'

			reply += '```Usage:```\n'

			reply += f'**{desktop_prefix} dutyorder**\n'
			reply += 'This will display the current agenda and meeting minutes notetaking order, as well as who\'s next on each list.\n'
			reply += 'Note: See how to set the agenda and minutes orders in the "set" command info.'

			await safe_reply(message, reply)
		# if the info on the alert command was requested
		elif command == 'alert':
			# list of string lines that the bot will reply to the help command with
			reply = f'`{command}:` Sets the channel that I send meeting and birthday alerts in and displays what the alert channel is set to.\n\n'

			reply += '```Usages:```\n'

			reply += f'**{desktop_prefix} alert here**\n'
			reply += 'This will set the channel that I send meeting and birthday alerts in to the channel that the command was sent in.\n\n'

			reply += f'**{desktop_prefix} alert channel**\n'
			reply += 'This will display what channel I am currently using as the alert channel.'

			await safe_reply(message, reply)
		# if the info on the bdays command was requested
		elif command == 'bdays':
			# list of string lines that the bot will reply to the help command with
			reply = f'`{command}:` Displays all birthdays I am currently keeping track of.\n\n'

			reply += '```Usage:```\n'

			reply += f'**{desktop_prefix} bdays**\n'
			reply += 'This will display all birthdays that I am currently keeping track of to say happy birthday to.\n'
			reply += 'Note: See how to add and remove birthdays in the "add" and "remove" command infos.'

			await safe_reply(message, reply)
		# if no argument was given or it isn't recognized
		else:
			# list of commands that the bot has
			command_list = ['help', 'add', 'remove', 'meetings', 'set', 'dutyorder', 'alert', 'bdays']

			# list of string lines that the bot will reply to the help command with
			reply = f'`Usage:` **{desktop_prefix} [command] [arguments...]**\n\n'
			reply += f'Type "{desktop_prefix} help [command]" to get more info on how to use a specific command.\n\n'

			reply += f'```List of commands:```\n'

			# add a numbered line for each command the bot has
			for i in range(len(command_list)):
				reply += f'**{i + 1}. {command_list[i]}**\n'
			
			reply += '\n```Notes:```\n'

			reply += '- I will `@everyone` 30 minutes before and at the start of every meeting and weekly meeting.\n'
			reply += '- I will show who is on agenda and meeting minutes duty every time I give a meeting alert.\n'
			reply += '- I will increment to the next person on meeting minutes duty after every meeting.\n'
			reply += '- I will increment to the next person on both agenda and meeting minutes duty after every weekly meeting.\n'
			reply += f'- I only processes times in the timezone that I am running in (currently {tzstr}).\n\n'

			reply += '**Maximum Number of:**\n'
			reply += f'Meetings: {ServerData.max_meetings}\n'
			reply += f'Weekly Meetings: {ServerData.max_weekly_meetings}\n'
			reply += f'Names on Agenda Duty: {ServerData.max_agenda_order}\n'
			reply += f'Names on Meeting Minutes Duty: {ServerData.max_minutes_order}\n'
			reply += f'Birthdays: {ServerData.max_bdays}\n'
			reply += f'Servers I can be in: {ServerData.max_servers}\n\n'

			# if the bot runner has supplied contact info to refer to
			if contact_info != '':
				reply += f'Contact my admin if you are having problems ({contact_info}).\n'
			reply += 'If you want more info, visit the repository for my code at https://github.com/ChandlerJayCalkins/Capstone-Meeting-Bot !'
			
			await safe_reply(message, reply)
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
					now = datetime.datetime.now(timezone)
					meeting = datetime.datetime(now.year, month, day, hour=hour, minute=minute, tzinfo=timezone)
					# if the meeting date is before now, increment it by a year
					if meeting < now:
						meeting = datetime.datetime(now.year + 1, month, day, hour=hour, minute=minute, tzinfo=timezone)
				else:
					await react_with_x(message)
					return
			# if a year was inputted
			else:
				if valid_date(day, month, year=year):
					meeting = datetime.datetime(year, month, day, hour=hour, minute=minute, tzinfo=timezone)
					now = datetime.datetime.now(timezone)
			
			# add meeting to list

			# if the meeting time is successfully added to the list
			if await server_data[message.guild].add_meeting(meeting):
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
			
			# construct object
			meeting = WeeklyMeeting(day, hour, minute)

			# if the meeting time is successfully added to the list in order and is not a duplicate
			if await server_data[message.guild].add_weekly_meeting(meeting):
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
					now = datetime.datetime.now(timezone)
					bday = datetime.datetime(now.year, month, day, hour=hour, minute=minute, tzinfo=timezone)
					# if the meeting date is before today, increment it by a year
					if bday.month < now.month or (bday.month == now.month and bday.day < now.day):
						bday = datetime.datetime(now.year + 1, month, day, hour=hour, minute=minute, tzinfo=timezone)
				else:
					await react_with_x(message)
					return
			# if a year was inputted
			else:
				await react_with_x(message)
				return
			
			# create bday object
			bday = BDay(bday, ' '.join(command[5:]))
			# if the bday was successfully added to the bday list
			if await server_data[message.guild].add_bday(bday):
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
			if await server_data[message.guild].remove_meetings(command[2:]):
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
					now = datetime.datetime.now(timezone)
					meeting = datetime.datetime(now.year, month, day, hour=hour, minute=minute, tzinfo=timezone)
					# if the meeting date is before now, increment it by a year
					if meeting < now:
						meeting = datetime.datetime(now.year + 1, month, day, hour=hour, minute=minute, tzinfo=timezone)
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
				# if this program is being run on windows
				if sys.platform == 'win32':
					meeting_str = server_data[message.guild].meetings[i].strftime(f'%A %b %#d %Y at %#H:%M / %#I:%M %p {tzstr}')
				# if this program is being run on linux, mac os, or any other os
				else:
					meeting_str = server_data[message.guild].meetings[i].strftime(f'%A %b %-d %Y at %-H:%M / %-I:%M %p {tzstr}')
				
				reply += f'**{i+1}. {meeting_str}**\n\n'

		reply += '```Weekly Meetings```\n'

		# if there are no weekly meetings
		if len(server_data[message.guild].display_weekly_meetings) < 1:
			reply += '**No weekly meetings.**\n'
		# if there is at least 1 weekly meeting
		else:
			# display all of the weekly meetings in a numbered list
			for i in range(len(server_data[message.guild].display_weekly_meetings)):
				reply += f'**{i+1}. {server_data[message.guild].display_weekly_meetings[i]}**\n\n'
		
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
			
			# if agenda list was passed as an argument and the agenda order was successfully set
			if command[1] == 'agenda' and server_data[message.guild].set_agenda_order(name_list):
				await react_with_check(message)
			# if the minutes list was passed as an argument and the minutes orer was successfully set
			elif command[1] == 'minutes' and server_data[message.guild].set_minutes_order(name_list):
				await react_with_check(message)
			# if the argument isn't recognized
			else:
				await react_with_x(message)
				return
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
	# if the command has an argument
	if len(command) > 1:
		# set the argument to lowercase to make it easier to compare
		command[1] = command[1].lower()
		# if the command follows the format "alert here"
		if command[1] == 'here':
			# set the alert channel for the server to the one that the command was sent in
			if server_data[message.guild].set_alert_channel(message.channel):
				await react_with_check(message)
			else:
				await react_with_check(message)
		# if the command follows the format "alert channel"
		elif command[1] == 'channel':
			channel_perms = message.channel.permissions_for(message.guild.me)
			# if the bot has permission to send messages in the channel of the message
			if channel_perms.send_messages:
				# if the bot doesn't have an alert channel
				if server_data[message.guild].alert_channel not in message.guild.text_channels:
					# look for one again
					server_data[message.guild].alert_channel = ServerData.find_first_message_server(message.guild)
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
# utility functions
#
########################################################################################################################

# iserts obj into l with a binary insert
# low = lowest index to insert into, high = highest index to insert into, no_dupes = returning false if obj is already in l within the low and high indexes
def bin_insert(l: list, obj, low = 0, high=None, no_dupes=False):
	# if no high argument was given, set it to the last index in l
	if high is None:
		high = len(l) - 1
	
	# if there are no duplicates allowed
	if no_dupes:
		# while the index to insert into hasn't been found yet
		while low <= high:
			# get the midpoint between the high and low indexes
			mid = (low + high) // 2
			# if the object is the same as the object at the midpoint in l
			if obj == l[mid]:
				return False
			
			# if the object is less than the object at the midpoint in l
			if obj < l[mid]:
				# cut the check to the lower half of the remaining list
				high = mid - 1
			# if the object is greater than or equal to the object at the midpoint in l
			else:
				# cut the check to the upper half of the remaining list
				low = mid + 1
	# if duplicates are allowed
	else:
		# while the index to insert into hasn't been found yet
		while low <= high:
			# get the midpoint between the high and low indexes
			mid = (low + high) // 2
			# if the object is less than the object at the midpoint in l
			if obj < l[mid]:
				high = mid - 1
			# if the object is greater than or equal to the object at the midpoint in l
			else:
				low = mid + 1
			
	# return the new list with obj inserted in its sorted position
	return l[:low] + [obj] + l[low:]

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

# sends a message in a channel and handles lack of permissions and character overflow
# returns true if the bot had permission to send messages in this channel at the start of this function, false if it didn't
async def safe_message(channel, message: str) -> bool:
	channel_perms = channel.permissions_for(channel.guild.me)
	# if the bot has permission to send messages in the channel of the message
	if channel_perms.send_messages:
		# while the reply is too long to send, find a split point before the message limit and send the reply up to that point
		while (len(message) > max_message_len):
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
					split_index = message.rfind(split_strs[i], 0, max_message_len)
					# if an instance of the string was found, use the index of that string as the split index
					if split_index != -1:
						split_index += 1
						break
			
			channel_perms = channel.permissions_for(channel.guild.me)
			# check to make sure the bot still has permission to send messages in this channel
			if channel_perms.send_messages:
				# send the part of the reply up to the split index
				await message.message(message[:split_index])
			# if it doesn't, then exit the loop
			else:
				break
			# remove the part of the reply that was just sent
			message = message[split_index:]
		
		channel_perms = channel.permissions_for(channel.guild.me)
		# check to make sure the bot still has permission to send messages in this channel
		if channel_perms.send_messages:
			# send the remaining part of the reply that is less than the max message length
			await channel.send(message)
		
		# return true if the bot had permission to send messages in this channel at the start of this function
		return True
	# if the bot doesn't have permission to send messages in the channel of the message
	else:
		return False

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
	token = token.lower()
	return token == 'm' or token == 'mo' or token == 'mon' or token == 'monday' or token == 'mondays'

def is_tuesday(token: str) -> bool:
	token = token.lower()
	return token == 'tu' or token == 'tue' or token == 'tues' or token == 'tuesday' or token == 'tuesdays'

def is_wednesday(token: str) -> bool:
	token = token.lower()
	return token == 'w' or token == 'we' or token == 'wed' or token == 'wednesday' or token == 'wednesdays'

def is_thursday(token: str) -> bool:
	token = token.lower()
	return token == 'th' or token == 'thu' or token == 'thur' or token == 'thurs' or token == 'thursday' or token == 'thursdays'

def is_friday(token: str) -> bool:
	token = token.lower()
	return token == 'f' or token == 'fr' or token == 'fri' or token == 'friday' or token == 'fridays'

def is_saturday(token: str) -> bool:
	token = token.lower()
	return token == 'sa' or token == 'sat' or token == 'saturday' or token == 'saturdays'

def is_sunday(token: str) -> bool:
	token = token.lower()
	return token == 'su' or token == 'sun' or token == 'sunday' or token == 'sundays'

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