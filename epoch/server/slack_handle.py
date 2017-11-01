#!/usr/bin/env python

# local modules
from component import user
from component import user_session
from component import repo
from util import slack_api
from settings import settings

# python modules
from flask import Response
import time
import datetime
import json

# the icon's url used in the bot that sends the response
ICON_URL = settings.getSettings().company_icon
COMPANY_NAME = settings.getSettings().company_name
COMPANY_URL = settings.getSettings().company_url

# configure a Slack server in order to send messages TO Slack
slack_server = settings.getSlack()

def parse_request(data_form):
	'''
	Parses the request using the specified data_form.

	Args:
		data_form: The data form from the request

	Returns:
		A response object based off of how the request was parsed.
	'''

	# TODO: add try/except here

	# grab the text information and determine the command
	args = data_form['text']
	if args is not None:
		command = args.split(' ')[0].upper()

		# create the user representation for this player
		user_obj = user.User(data_form['user_id'], data_form['user_name'])

		# does this user exist as a user?
		exists = user.exists(user_obj.uuid)
		if exists:
			return handle_command(user_obj, command, data_form)
		else:
			return Response('Your user does not exist! Please contact Stephen/Jed.'), 200
	else:
		return Response('Unknown command specified.'), 200

def handle_command(user_obj, command, data):
	'''
	Handles the command given by the request.

	Args:
		user_obj: The object that represents the user
		command: The command from the request
		data: The data form that is the request

	Returns:
		A response object based off of how the request's command was handled.
	'''

	# get the current state of the user
	state = user_session.get_state(user_obj.uuid)

	if command == 'START':
		if state == 'OFFLINE':

			# set the new state
			user_session.set_state(user_obj.uuid, 'ONLINE')
			user.log_state_change(user_obj.uuid, 'ONLINE', 'OFFLINE')

			# the timestamp needs updated
			user_session.set_work_time(user_obj.uuid, 0)
			user_session.set_session_timestamp(user_obj.uuid)

			# send slack message to channel
			slack_server.send_message(contents=str(user_obj.username) + ' is now online!', channel='#work-progress', username='Epoch Bot', icon_emoji=':green_heart:')

			return Response(response=json.dumps(build_login_response(user_obj)), status=200, mimetype='application/json')
		else:
			return Response('In order to use [start], you must be in OFFLINE mode. You are in ' + str(state) + ' mode!'), 200
	elif command == 'STOP':
		if state == 'ONLINE':

			# set the new state
			user_session.set_state(user_obj.uuid, 'OFFLINE')
			user.log_state_change(user_obj.uuid, 'OFFLINE', 'ONLINE')

			# get how long they worked
			msecs = user_session.get_work_time(user_obj.uuid)
			start_time = user_session.get_session_timestamp(user_obj.uuid)
			end_time = time.strftime('%Y-%m-%d %H:%M:%S')

			# get the user's goal hours
			goal_hours = user.determine_goal_hours_today(user_obj.uuid)
			worked_hours = '%.2f' % (msecs / 3600000.0)

			# create the session log
			user_session.create_user_session_log(user_obj.uuid, msecs, start_time, end_time)

			# reset their work time to 0
			user_session.set_work_time(user_obj.uuid, 0)
			user_session.set_session_timestamp(user_obj.uuid)

			# send slack message to channel
			slack_server.send_message(contents=str(user_obj.username) + ' is now offline...', channel='#work-progress', username='Epoch Bot', icon_emoji=':broken_heart:')

			# construct a payload that shows the commit logs
			handle_logout_payload(user_obj, start_time, end_time, worked_hours, goal_hours)
			
			return Response(response=json.dumps(build_logout_response(user_obj)), status=200, mimetype='application/json')
		else:
			return Response('In order to use [stop], you must be in ONLINE mode. You are in ' + str(state) + ' mode!'), 200
	elif command == 'RESUME':
		if state == 'PAUSED':

			# set the new state
			user_session.set_state(user_obj.uuid, 'ONLINE')
			user.log_state_change(user_obj.uuid, 'ONLINE', 'PAUSED')

			# send slack message to channel
			slack_server.send_message(contents=str(user_obj.username) + ' is back from their break!', channel='#work-progress', username='Epoch Bot', icon_emoji=':green_heart:')
			
			return Response(response=json.dumps(build_resume_response(user_obj)), status=200, mimetype='application/json')
		else:
			return Response('In order to use [resume], you must be in PAUSED mode. You are in ' + str(state) + ' mode!'), 200
	elif command == 'PAUSE':
		if state == 'ONLINE':

			# set the new state
			user_session.set_state(user_obj.uuid, 'PAUSED')
			user.log_state_change(user_obj.uuid, 'PAUSED', 'ONLINE')

			# send slack message to channel
			slack_server.send_message(contents=str(user_obj.username) + ' went for a break!', channel='#work-progress', username='Epoch Bot', icon_emoji=':yellow_heart:')

			return Response(response=json.dumps(build_pause_response(user_obj)), status=200, mimetype='application/json')
		else:
			return Response('In order to use [pause], you must be in ONLINE mode. You are in ' + str(state) + ' mode!'), 200
	elif command == 'INFO':
		return Response(response=json.dumps(build_info_response(user_obj)), status=200, mimetype='application/json')
	elif command == 'STATUS':

		# temporarirly removes auth check
		# check if it's an authorized user
		if user_obj.username == 'stephen' or user_obj.username == 'peraldon' or 1==1:
			return Response(response=json.dumps(build_status_response(user_obj)), status=200, mimetype='application/json')
		else:
			return Response('You are not authorized for this command.'), 200
	
	return Response('Unknown command! Try /epoch [start|stop|pause|resume|info]'), 200

def build_login_response(user_obj):
	'''
	Builds the login response for the specified user.

	Args:
		user_obj: The object representation for the specified user

	Returns:
		The Python dictionary that can be converted to JSON and sent as a response.
	'''

	# create the attachment
	contents = {}
	contents['title'] = COMPANY_NAME
	contents['title_link'] = COMPANY_URL
	contents['color'] = "good"

	# Determine the text of the attachment
	contents['text'] = 'You have started a new Epoch session. You are now ONLINE.'

	# build the hours 
	fields = []
	f1 = {}
	f1['title'] = 'Goal Hours (today)'
	f1['value'] = user.determine_goal_hours_today(user_obj.uuid)
	f1['short'] = True
	f2 = {}
	f2['title'] = 'Total Hours (month)'
	f2['value'] = user_session.get_total_worked(user_obj.uuid)
	f2['short'] = True
	fields.append(f1)
	fields.append(f2)
	contents['fields'] = fields

	# attach the footer
	_attach_footer(contents)

	# construct the response message with the attachment
	message = slack_api.Message()
	message.add_attachment(contents)
	return message.get_contents()

def build_logout_response(user_obj):
	'''
	Builds the logout response for the specified user.

	Args:
		user_obj: The object representation for the specified user

	Returns:
		The Python dictionary that can be converted to JSON and sent as a response.
	'''

	# create the attachment
	contents = {}
	contents['title'] = COMPANY_NAME
	contents['title_link'] = COMPANY_URL
	contents['color'] = "danger"

	# Determine the text of the attachment
	contents['text'] = 'You are now logged out of Epoch, changing your state to OFFLINE.'

	# build the hours 
	fields = []
	f1 = {}
	f1['title'] = 'Total Hours (month)'
	f1['value'] = '%.2f' % (user_session.get_total_worked(user_obj.uuid))
	f1['short'] = True
	f2 = {}
	f2['title'] = 'Goal Hours (month)'
	f2['value'] = user.get_goal_total(user_obj.uuid)
	f2['short'] = True
	fields.append(f1)
	fields.append(f2)
	contents['fields'] = fields

	# attach the footer
	_attach_footer(contents)

	# construct the response message with the attachment
	message = slack_api.Message()
	message.add_attachment(contents)
	return message.get_contents()

def build_pause_response(user_obj):
	'''
	Builds the pause response for the specified user.

	Args:
		user_obj: The object representation for the specified user

	Returns:
		The Python dictionary that can be converted to JSON and sent as a response.
	'''

	# create the attachment
	contents = {}
	contents['title'] = COMPANY_NAME
	contents['title_link'] = COMPANY_URL
	contents['color'] = "warning"

	# Determine the text of the attachment
	contents['text'] = 'You have paused your session. Enjoy your break! Resume with /epoch resume.'

	# attach the footer
	_attach_footer(contents)

	# construct the response message with the attachment
	message = slack_api.Message()
	message.add_attachment(contents)
	return message.get_contents()

def build_resume_response(user_obj):
	'''
	Builds the resume response for the specified user.

	Args:
		user_obj: The object representation for the specified user

	Returns:
		The Python dictionary that can be converted to JSON and sent as a response.
	'''

	# create the attachment
	contents = {}
	contents['title'] = COMPANY_NAME
	contents['title_link'] = COMPANY_URL
	contents['color'] = "good"

	# Determine the text of the attachment
	contents['text'] = 'You have resumed your session. Welcome back!'

	# attach the footer
	_attach_footer(contents)

	# construct the response message with the attachment
	message = slack_api.Message()
	message.add_attachment(contents)
	return message.get_contents()

def build_info_response(user_obj):
	'''
	Builds the info response for the specified user.

	Args:
		user_obj: The object representation for the specified user

	Returns:
		The Python dictionary that can be converted to JSON and sent as a response.
	'''
	# get the state of the user
	state = user_session.get_state(user_obj.uuid)

	# create the attachment
	contents = {}
	contents['title'] = COMPANY_NAME
	contents['title_link'] = COMPANY_URL

	# color the attachment based off of state
	if state == 'ONLINE':
		contents['color'] = "good"
	elif state == 'OFFLINE':
		contents['color'] = "danger"
	elif state == 'PAUSED':
		contents['color'] = "warning"

	# Determine the text of the attachment
	contents['text'] = 'Your current state is ' + str(state) + '.'

	if state == 'ONLINE' or state == 'PAUSED':

		work_time = user_session.get_work_time(user_obj.uuid)

		# build the hours 
		fields = []
		f1 = {}
		f1['title'] = 'Worked Time (session)'
		f1['value'] = '%.2f' % (work_time / 3600000.0)
		f1['short'] = True
		f2 = {}
		f2['title'] = 'Total Hours (month)'
		f2['value'] = user_session.get_total_worked(user_obj.uuid)
		f2['short'] = True
		fields.append(f1)
		fields.append(f2)
		contents['fields'] = fields
	elif state == 'OFFLINE':
		# build the hours 
		fields = []
		f1 = {}
		f1['title'] = 'Total Hours (month)'
		f1['value'] = user_session.get_total_worked(user_obj.uuid)
		f1['short'] = True
		f2 = {}
		f2['title'] = 'Goal Hours (month)'
		f2['value'] = user.get_goal_total(user_obj.uuid)
		f2['short'] = True
		fields.append(f1)
		fields.append(f2)
		contents['fields'] = fields

	# attach the footer
	_attach_footer(contents)

	# construct the response message with the attachment
	message = slack_api.Message()
	message.add_attachment(contents)
	return message.get_contents()

def build_status_response(user_obj):
	'''
	Builds the status response for the specified user.

	Args:
		user_obj: The object representation for the specified user

	Returns:
		The Python dictionary that can be converted to JSON and sent as a response.
	'''

	# USER --- STATE --- LAST LOGIN --- HOURS WORKED --- GOAL HOURS
	all_users = user.get_all_users()
	if all_users is not None and len(all_users) > 0:

		# construct the response message with the attachment
		message = slack_api.Message()

		for uuid, name in all_users:
			state = user_session.get_state(uuid)
			last_login = user_session.get_session_timestamp(uuid)
			total_hours = '%.2f' % user_session.get_total_worked(uuid)
			goal_hours = user.get_goal_total(uuid)

			data = (name, state, last_login, total_hours, goal_hours)

			# create the attachment
			contents = {}
			contents['title'] = str(name)

			# TODO maybe a link to our workers page?
			contents['title_link'] = COMPANY_URL

			# color the attachment based off of state
			if state == 'ONLINE':
				contents['color'] = "good"
			elif state == 'OFFLINE':
				contents['color'] = "danger"
			elif state == 'PAUSED':
				contents['color'] = "warning"

			# Determine the text of the attachment
			#contents['text'] = 'Last state change at ' + str(last_login) + ' EST.'

			# build the hours 
			fields = []
			f1 = {}
			f1['title'] = 'Total Hours (month)'
			f1['value'] = total_hours
			f1['short'] = True
			f2 = {}
			f2['title'] = 'Goal Hours (month)'
			f2['value'] = goal_hours
			f2['short'] = True
			fields.append(f1)
			fields.append(f2)
			contents['fields'] = fields

			if type(contents) is dict:

				# general footer
				contents['footer'] = 'Epoch API'
				contents['footer_icon'] = ICON_URL

				if last_login is not None:
		
					# attach the timestamp
					contents['ts'] = int(last_login.strftime('%s'))

			# add the attachment
			message.add_attachment(contents)

		return message.get_contents()
	else:
		return Response('Unexpected error occurred locally when parsing STATE request.'), 200

def handle_logout_payload(user_obj, start_date, end_date, worked_hours, goal_hours):
	'''
	Builds the logout payload for the specified user.

	Args:
		user_obj: The object representation for the specified user
		start_date: The timestamp for when they logged in
		end_date: The timestamp for when they logged out
		worked_hours: The worked hours for the day
		goal_hours: The goal hours for the day

	Returns:
		The Python dictionary that can be converted to JSON and sent as a post.
	'''
	commits = repo.get_commit_logs(user_obj.uuid, start_date, end_date)

	# construct an empty message
	message = slack_api.Message()

	# create the attachment
	contents = {}
	contents['color'] = "#082b63"
	contents['title'] = str(user_obj.username)
	contents['title_link'] = COMPANY_URL

	# build the text
	if commits is not None and len(commits) > 0:

		text_builder = ''

		for repo_name, commit_text, commit_url in commits:
			parts = commit_text.splitlines()
			m = '`<' + str(commit_url) + '|' + str(repo_name) + '>`: ' + str(parts[0]) + '\n'
			text_builder = text_builder + m

		contents['text'] = text_builder

	# build the hours 
	fields = []
	f1 = {}
	f1['title'] = 'Session Hours (today)'
	f1['value'] = worked_hours
	f1['short'] = True
	f2 = {}
	f2['title'] = 'Goal Hours (today)'
	f2['value'] = goal_hours
	f2['short'] = True
	fields.append(f1)
	fields.append(f2)
	contents['fields'] = fields

	# attach the footer
	_attach_footer(contents)

	# add the attachment
	message.add_attachment(contents)
	message_data = message.get_contents()
	message_data['channel'] = '#work-submit'
	message_data['username'] = 'Epoch Bot'
	message_data['icon_emoji'] = ':bar_chart:'

	# send it off
	slack_server.send_json(message_data)

def _attach_footer(contents):
	'''
	Attach the footer to the Python dictionary contents.

	Args:
		contents: The contents that needs to have a footer

	Returns:
		The same contents, except the footer added. If unable to add the 
		footer, returns the same object.
	'''
	if type(contents) is dict:

		# general footer
		contents['footer'] = 'Epoch API'
		contents['footer_icon'] = ICON_URL

		# attach the timestamp
		contents['ts'] = int(time.time())

	return contents
