#!/usr/bin/python

# local imports
from component import user
from component import user_session
from component import repo
from settings import settings
from util import slack_api

# python modules
import sys
import datetime
import time

# the icon's url used in the bot that sends the response
ICON_URL = settings.getSettings().company_icon

# configure a Slack server in order to send messages TO Slack
slack_api_url = settings.getSettings().slack_api_url
slack_headers = {'content-type': 'application/json'}
slack_server = slack_api.SlackAPI(api_url=slack_api_url, headers=slack_headers)

def handle_help_command():
	'''
	Handles the parsing of the help command.
	'''
	print('This module is invoked in the following ways: \n')
	print('python track.py help')
	print('- Display this message.\n')
	print('python track.py add')
	print('- Add a session log/timestamp for a user.\n')
	print('python track.py remove')
	print('- Remove a session log/timestamp from a user.\n')
	print('python track.py modify')
	print('- Change a session log/timestamp\'s worked hours for a user.\n')
	print('python track.py list')
	print('- List the status of all users\n')
	print('python track.py session')
	print('- List session log/timestamps for a user.\n')
	print('python track.py verify')
	print('- Verify and sign timestamps for a user.\n')
	print('python track.py report')
	print('- Generate session reports for a user, and send it to them!\n')

def handle_list_command():
	'''
	Handles the parsing of the list command. This allows the user to see what 
	users we are tracking.
	'''

	# USER --- STATE --- LAST LOGIN --- HOURS WORKED --- GOAL HOURS
	all_users = user.get_all_users()
	if all_users is not None and len(all_users) > 0:
		for uuid, name in all_users:
			state = user_session.get_state(uuid)
			last_login = user_session.get_session_timestamp(uuid)
			total_hours = '%.2f' % user_session.get_total_worked(uuid)
			goal_hours = user.get_goal_total(uuid)

			data = (name, state, last_login, total_hours, goal_hours)

			print('[' + str(name) + '][' + str(state) + '] was last seen at ' + str(last_login) + '. They are at ' + str(total_hours) + ' / ' + str(goal_hours) + ' hours.')

def handle_add_command():
	'''
	Handles the parsing of the add command. This allows the user to manually add
	a session log to the database.
	'''
	verify_username = raw_input('What is your Slack username (Ex: stephen)?: ')
	if verify_username is None:
		print('You must provide your name to sign session timestamps!')
		return None

	verify_data = user.get_user(verify_username)
	if verify_data is None:
		print('Unable to find your name ' + str(verify_username) + '.')
		return None

	# get the uuid of the person verifying
	verify_uuid = str(verify_data[0])

	req_name = raw_input('Name of the user to add a session log for (Ex: stephen)?: ')
	if req_name is None:
		print('You must provide the name of the user!')
		return None

	user_data = user.get_user(req_name)
	if user_data is None:
		print('Unable to find ' + str(req_name) + '. Are you sure they exist?')
		return None

	start_date = raw_input('The date of the session log (Ex: YYYY-MM-DD)?: ')
	if start_date is None:
		print('You must provide a valid start date, such as 2016-11-16')
		return None

	# attempt to format their input
	try:
		s_year, s_month, s_day = _format_date(start_date)
	except Exception as e:
		print(e)
		print('Unable to convert date to representation... Are you sure it was entered correctly?')
		return None

	worked_hours = raw_input('Number of hours for this session log (Ex: 2.5)?: ')
	if worked_hours is None:
		print('You must enter their worked hours!')
		return None

	# attempt to format their input
	try:
		worked_hours_ms = float(worked_hours) * 3600000
	except Exception as e:
		print(e)
		print('Unable to convert hours to representation... Are you sure it was entered correctly?')
		return None

	# add to their session log
	user_session.create_user_session_log(user_data[0], worked_hours_ms, start_date, start_date, verify_uuid)

	print('Successfully added ' + str(worked_hours) + ' to ' + str(req_name) + '\'s session log for ' + str(start_date))

def handle_remove_command():
	'''
	Handles the parsing of the remove command. This allows the user to manually remove
	a session log from the database.
	'''
	verify_username = raw_input('What is your Slack username (Ex: stephen)?: ')
	if verify_username is None:
		print('You must provide your name to sign session timestamps!')
		return None

	verify_data = user.get_user(verify_username)
	if verify_data is None:
		print('Unable to find your name ' + str(verify_username) + '.')
		return None

	# get the uuid of the person verifying
	verify_uuid = str(verify_data[0])

	req_name = raw_input('Name of the user to remove a session log from (Ex: stephen)?: ')
	if req_name is None:
		print('You must provide the name of the user!')
		return None

	user_data = user.get_user(req_name)
	if user_data is None:
		print('Unable to find ' + str(req_name) + '. Are you sure they exist?')
		return None

	start_date = raw_input('The date of the session log (Ex: YYYY-MM-DD)?: ')
	if start_date is None:
		print('You must provide a valid start date, such as 2016-11-16')
		return None

	# attempt to format their input
	try:
		s_year, s_month, s_day = _format_date(start_date)
	except Exception as e:
		print(e)
		print('Unable to convert date to representation... Are you sure it was entered correctly?')
		return None

	# delete session log
	user_session.delete_user_session_log(user_data[0], start_date)
	print('Successfully deleted ' + str(req_name) + '\'s session log for ' + str(start_date) + ' if it existed!')

def handle_modify_command():
	'''
	Handles the parsing of the modify command. This allows the user to manually change
	the time worked for a session log in the database.
	'''
	verify_username = raw_input('What is your Slack username (Ex: stephen)?: ')
	if verify_username is None:
		print('You must provide your name to sign session timestamps!')
		return None

	verify_data = user.get_user(verify_username)
	if verify_data is None:
		print('Unable to find your name ' + str(verify_username) + '.')
		return None

	# get the uuid of the person verifying
	verify_uuid = str(verify_data[0])

	req_name = raw_input('Name of the user to modify a session log for (Ex: stephen)?: ')
	if req_name is None:
		print('You must provide the name of the user!')
		return None

	user_data = user.get_user(req_name)
	if user_data is None:
		print('Unable to find ' + str(req_name) + '. Are you sure they exist?')
		return None

	start_date = raw_input('The date of the session log (Ex: YYYY-MM-DD)?: ')
	if start_date is None:
		print('You must provide a valid start date, such as 2016-11-16')
		return None

	# attempt to format their input
	try:
		s_year, s_month, s_day = _format_date(start_date)
	except Exception as e:
		print(e)
		print('Unable to convert date to representation... Are you sure it was entered correctly?')
		return None

	worked_hours = raw_input('Number of hours the log should be set to (Ex: 2.5)?: ')
	if worked_hours is None:
		print('You must enter their worked hours!')
		return None

	# attempt to format their input
	try:
		worked_hours_ms = float(worked_hours) * 3600000
	except Exception as e:
		print(e)
		print('Unable to convert hours to representation... Are you sure it was entered correctly?')
		return None

	# add to their session log
	user_session.update_user_session_log(user_data[0], worked_hours_ms, start_date, verify_uuid)
	print('Successfully modified ' + str(req_name) + '\'s session log for ' + str(start_date) + ' and set their worked hours to ' + str(worked_hours) + ' hours.')

def handle_session_command():
	'''
	Handles the parsing of the session command. This allows the user to print
	session information about a user.
	'''
	req_name = raw_input('What is the name of the user you wish to list session information (Ex: stephen)?: ')
	if req_name is None:
		print('You must provide the name of the user!')
		return None

	user_data = user.get_user(req_name)
	if user_data is None:
		print('Unable to find ' + str(req_name) + '. Are you sure they exist?')
		return None

	start_date = raw_input('The starting date to query for the user (Ex: YYYY-MM-DD)?: ')
	if start_date is None:
		print('You must provide a valid start date, such as 2016-11-16')
		return None

	end_date = raw_input('The ending date to query for the user (Ex: YYYY-MM-DD)?: ')
	if end_date is None:
		print('You must provide a valid end date, such as 2016-11-16')
		return None

	# attempt to format their input
	try:
		s_year, s_month, s_day = _format_date(start_date)
		e_year, e_month, e_day = _format_date(end_date)
	except Exception as e:
		print(e)
		print('Unable to convert dates to representation... Are you sure they are entered correctly?')
		return None

	# convert to timestamp that SQL knows
	start_date = datetime.datetime(s_year, s_month, s_day, 0, 0, 0).strftime('%Y-%m-%d %H:%M:%S')
	end_date = datetime.datetime(e_year, e_month, e_day, 0, 0, 0).strftime('%Y-%m-%d %H:%M:%S')

	# get all their session logs
	session_info = user_session.get_session_logs(user_data[0], start_date, end_date)

	if session_info is not None and len(session_info) > 0:

		print('\nDisplaying session info for ' + str(req_name) + ' between ' + str(start_date) + ' and ' + str(end_date) + ': \n')
		
		# iterate and print
		for log_id, user_id, work_time, start, end, approved in session_info:
			hours = '%.2f' % (work_time / 3600000.0)

			if approved == 'None':
				approved = False

			print('Log ID #' + str(log_id) + ' shows ' + str(hours) + ' hours of work starting on ' + str(start) + '. [Approved=' + str(approved) + ']')
	else:
		print('No found session information for ' + str(req_name) + ' in the time period of ' + str(start_date) + ' and ' + str(end_date))

def handle_report_command():
	'''
	Handles the parsing of the report command. This allows the user to print
	session information about a user and get detailed information about them.
	'''
	req_name = raw_input('Name of the user to generate the report for (Ex: stephen)?: ')
	if req_name is None:
		print('You must provide the name of the user!')
		return None

	user_data = user.get_user(req_name)
	if user_data is None:
		print('Unable to find ' + str(req_name) + '. Are you sure they exist?')
		return None

	start_date = raw_input('The starting date to query for the user (Ex: YYYY-MM-DD)?: ')
	if start_date is None:
		print('You must provide a valid start date, such as 2016-11-16')
		return None

	end_date = raw_input('The ending date to query for the user (Ex: YYYY-MM-DD)?: ')
	if end_date is None:
		print('You must provide a valid end date, such as 2016-11-16')
		return None

	# attempt to format their input
	try:
		s_year, s_month, s_day = _format_date(start_date)
		e_year, e_month, e_day = _format_date(end_date)
	except Exception as e:
		print(e)
		print('Unable to convert dates to representation... Are you sure they are entered correctly?')
		return None

	# convert to timestamp that SQL knows
	start_date = datetime.datetime(s_year, s_month, s_day, 0, 0, 0).strftime('%Y-%m-%d %H:%M:%S')
	end_date = datetime.datetime(e_year, e_month, e_day, 0, 0, 0).strftime('%Y-%m-%d %H:%M:%S')

	# get all their session logs
	session_info = user_session.get_session_logs(user_data[0], start_date, end_date)

	if session_info is not None and len(session_info) > 0:

		# sort the logs to verified/not
		not_verified = []
		verified = []
		for log_id, user_id, work_time, start, end, approved in session_info:
			if approved == 'None':
				not_verified.append((log_id, user_id, work_time, start, end, approved))
			else:
				verified.append((log_id, user_id, work_time, start, end, approved))

		# determine the time that was verified
		verified_time = 0
		for log_id, user_id, work_time, start, end, approved in verified:
			verified_time = verified_time + work_time

		# determine the time that was not verified
		not_verified_time = 0
		for log_id, user_id, work_time, start, end, approved in not_verified:
			not_verified_time = not_verified_time + work_time

		print('\nUser report for ' + str(req_name) + ' between ' + str(start_date) + ' and ' + str(end_date) + ': \n')
		
		verified_hours = '%.2f' % (verified_time / 3600000.0)
		not_verified_hours = '%.2f' % (not_verified_time / 3600000.0)
		print(str(len(not_verified)) + ' transactions were NOT VERIFIED totalling ' + str(not_verified_hours) + ' hours.\n')
		print(str(len(verified)) + ' transactions were VERIFIED totalling ' + str(verified_hours) + ' hours.\n')

		# determine if they've reached their goal
		goal_hours = user.get_goal_total(user_data[0])
		reached_goal = False
		failed_by_hours = goal_hours - float(verified_hours)
		if failed_by_hours <= 0:
			reached_goal = True

		print('The monthly goal hours for ' + str(req_name) + ' is ' + str(goal_hours))

		if reached_goal:
			print(str(req_name) + ' has reached their monthly goal!')
		else:
			print(str(req_name) + ' was ' + str(failed_by_hours) + ' hours short of their goal!')

		send_report = raw_input('Would you like to me to send this report to the user [Yes/No]?: ')
		if send_report is not None and (send_report.lower() == 'yes' or send_report.lower() == 'y'):
			send_user_report(user_data, start_date, end_date, verified_hours, not_verified_hours, goal_hours)

	else:
		print('No found session information for ' + str(req_name) + ' in the time period of ' + str(start_date) + ' and ' + str(end_date))

def send_user_report(user_obj, start_date, end_date, verified_hours, not_verified_hours, goal_hours):
	'''
	Builds the user report for the specified user.

	Args:
		user_obj: The object representation for the specified user
		start_date: The starting part of the interval
		end_date: The ending part of the interval
		verified_hours: Number of hours that were verified 
		not_verified_hours: Number of hours that weren't verified
		goal_hours: The goal hours for the user 
		
	Returns:
		The Python dictionary that can be converted to JSON and sent as a post.
	'''

	# format the time string representations to objects
	start = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
	end = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

	# format not verified hours
	not_ver_hrs = float(not_verified_hours)

	# construct an empty message
	message = slack_api.Message()

	# create the attachment
	contents = {}
	contents['color'] = "#082b63"
	contents['title'] = str(user_obj[1])
	contents['title_link'] = 'http://isles.io'

	if not_ver_hrs > 0:
		contents['pretext'] = 'Greetings, ' + str(user_obj[1]) + '. Here is your monthly report, minus ' + str(not_verified_hours) + ' hours that were not verified.'
	else:
		contents['pretext'] = 'Greetings, ' + str(user_obj[1]) + '. Here is your monthly report.'

	contents['text'] = 'Report from ' + str(start.strftime('%b %d, %Y')) + ' to ' + str(end.strftime('%b %d, %Y'))

	# build the hours 
	fields = []
	f1 = {}
	f1['title'] = 'Verified Hours '
	f1['value'] = verified_hours
	f1['short'] = True
	f2 = {}
	f2['title'] = 'Goal Hours'
	f2['value'] = goal_hours
	f2['short'] = True
	fields.append(f1)
	fields.append(f2)
	contents['fields'] = fields

	# general footer
	contents['footer'] = 'Epoch API'
	contents['footer_icon'] = ICON_URL

	# attach the timestamp
	contents['ts'] = int(time.time())

	# add the attachment
	message.add_attachment(contents)
	message_data = message.get_contents()
	message_data['channel'] = str(user_obj[0])
	message_data['username'] = 'Epoch Bot'
	message_data['icon_emoji'] = ':bar_chart:'

	# send it off
	slack_server.send_json(message_data)

def handle_verify_command():
	'''
	Handles the parsing of the verify command. This allows the user
	to sign session timestamps.
	'''
	verify_username = raw_input('What is your Slack username (Ex: stephen)?: ')
	if verify_username is None:
		print('You must provide your name to sign session timestamps!')
		return None

	verify_data = user.get_user(verify_username)
	if verify_data is None:
		print('Unable to find your name ' + str(verify_username) + '.')
		return None

	# get the uuid of the person verifying
	verify_uuid = str(verify_data[0])

	req_name = raw_input('Name of the user to verify timestamps for (Ex: stephen)?: ')
	if req_name is None:
		print('You must provide the name of the user!')
		return None

	user_data = user.get_user(req_name)
	if user_data is None:
		print('Unable to find ' + str(req_name) + '. Are you sure they exist?')
		return None

	start_date = raw_input('The starting date to verify for the user (Ex: YYYY-MM-DD)?: ')
	if start_date is None:
		print('You must provide a valid start date, such as 2016-11-16')
		return None

	end_date = raw_input('The ending date to verify for the user (Ex: YYYY-MM-DD)?: ')
	if end_date is None:
		print('You must provide a valid end date, such as 2016-11-16')
		return None

	# attempt to format their input
	try:
		s_year, s_month, s_day = _format_date(start_date)
		e_year, e_month, e_day = _format_date(end_date)
	except Exception as e:
		print(e)
		print('Unable to convert dates to representation... Are you sure they are entered correctly?')
		return None

	# convert to timestamp that SQL knows
	start_date = datetime.datetime(s_year, s_month, s_day, 0, 0, 0).strftime('%Y-%m-%d %H:%M:%S')
	end_date = datetime.datetime(e_year, e_month, e_day, 0, 0, 0).strftime('%Y-%m-%d %H:%M:%S')

	# get all their session logs
	session_info = user_session.get_session_logs(user_data[0], start_date, end_date)

	# if they have session logs
	if session_info is not None and len(session_info) > 0:

		# build a list of the not verified ones
		not_verified = []
		for log_id, user_id, work_time, start, end, approved in session_info:
			if approved == 'None':
				not_verified.append((log_id, user_id, work_time, start, end, approved))

		# if they have not verified ones
		if len(not_verified) > 0:
			print('\nDisplaying unapproved session timestamps for ' + str(req_name) + ' between ' + str(start_date) + ' and ' + str(end_date) + ': \n')

			not_verified_ids = []
			for log_id, user_id, work_time, start, end, approved in not_verified:
				hours = '%.2f' % (work_time / 3600000.0)
				not_verified_ids.append(log_id)
				print('Log ID #' + str(log_id) + ' shows ' + str(hours) + ' hours of work starting on ' + str(start) + '.')

			# allow the user to verify
			_handle_verify_session(verify_uuid, not_verified_ids)
		else:
			print('No unapproved session timestamps found for ' + str(req_name) + ' between ' + str(start_date) + ' and ' + str(end_date) + '.')
		
	else:
		print('No found session information for ' + str(req_name) + ' in the time period of ' + str(start_date) + ' and ' + str(end_date))

def _handle_verify_session(verify_uuid, not_verified):
	'''
	Handles the verifying of the session information. Prompts the user with 
	a message about which transactions to sign.

	Args:
		verify_uuid: The UUID of the signer
		not_verified: The list of IDs that are not verified
	'''

	print('\nYou can now enter the ID of the transactions you want to sign!')
	print('You can choose multiple at once. Ex: 1,2,3,4')

	loop = True
	while loop:
		trans = raw_input('Enter the ID of the transaction to verify (or all): ')
		if trans is None or trans == '':
			loop = False
			return None

		if type(trans) is str and trans.lower() in ['all']:
			# make a copy of not verified transactions
			copy_verified = not_verified[:]
			for not_ver_req in copy_verified:
				_verify_session(verify_uuid, not_verified, not_ver_req)
		else:
			parts = trans.split(',')
			if len(parts) > 0:
				for p in parts:
					_verify_session(verify_uuid, not_verified, p)
			else:
				_verify_session(verify_uuid, not_verified, trans)

def _verify_session(verify_uuid, not_verified_ids, trans_id):
	'''
	Verifies the session by signing with the verify_uuid.

	Args:
		verify_uuid: The UUID of the user verifying
		not_verified_ids: The list of ids that are not yet verified
		trans_id: The ID of the transaction the user is verifying
	'''
	try:
		transaction = int(trans_id)

		if transaction in not_verified_ids:
			user_session.verify_session_log(transaction, verify_uuid)
			not_verified_ids.remove(transaction)
			print('Signed transaction #' + str(transaction) + '!')
		else:
			print('Unknown transaction #' + str(trans_id) + '!')
	except Exception as e:
		print(e)
		print('Unable to verify transaction ' + str(trans_id) + '.')

def _format_date(input_date):
	'''
	Formats the string and returns the date representation for it.

	Args:
		The input date in the form of 'YYYY-MM-DD'

	Returns:
		The date in the form of (year, month, day) where each element is an int.
	'''

	parts = input_date.split("-")
	year = int(parts[0])
	month = int(parts[1])
	day = int(parts[2])

	return (year, month, day)

# if ran from command line
if __name__ == '__main__':

	if len(sys.argv) > 1:
		cmd = sys.argv[1].lower()

		if cmd == 'help':
			handle_help_command()
		elif cmd == 'report':
			handle_report_command()
		elif cmd == 'add':
			handle_add_command()
		elif cmd == 'remove':
			handle_remove_command()
		elif cmd == 'modify':
			handle_modify_command()
		elif cmd == 'list':
			handle_list_command()
		elif cmd == 'session':
			handle_session_command()
		elif cmd == 'verify':
			handle_verify_command()
		else:
			handle_help_command()
	else:
		handle_help_command()