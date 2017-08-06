#!/usr/bin/python

# local imports
from component import user
from component import user_session
from component import team
from settings import settings

# python modules
import requests
import json
import sys

# API Token for Slack, your app's xoxp- token (available on the Install App page)
TOKEN = settings.getSettings().slack_api_token

def get_all_possible_users():
	'''
	Get a list of all possible users on this Slack.

	Returns:
		A list of users in the form of (user_id, user_name) for this Slack.
	'''

	result = []

	payload = {'token': TOKEN}
	r = requests.get('https://slack.com/api/users.list', params=payload)

	if r is not None:
		response_data = r.json()

		# JSON format according to https://api.slack.com/methods/users.list
		members = response_data['members']
		for member in members:
			user_id = str(member['id'])
			user_name = str(member['name'])

			obj = (user_id, user_name)
			result.append(obj)

	return result

def get_not_yet_registered():
	'''
	Get a list of all the users and their information for those that have not
	been registered with Epoch.

	Returns:
		A list of users in the form of (user_id, user_name) for this Slack, 
		in which each user has yet to be registered.
	'''
	poss_users = get_all_possible_users()
	not_registered = []

	if poss_users is not None and len(poss_users) > 0:
		for p_uuid, p_name in poss_users:
			exists = user.exists(p_uuid)
			if not exists:
				not_registered.append((p_uuid, p_name))

	return not_registered

def get_slack_uuid(username):
	'''
	Get the slack uuid for the user with the specified username.

	Args:
		username: The username of the slack user

	Returns:
		The uuid for the specified slack user.
	'''
	possible_users = get_all_possible_users()
	if possible_users is not None and len(possible_users) > 0:
		for p_uuid, p_name in possible_users:
			if username == p_name:
				return p_uuid

	return None

def handle_create_team():
	'''
	Handles the creation of a team.
	'''
	print('----- ----- ----- -----')
	print('---- Team Creation ---- ')
	print('----- ----- ----- -----')
	print('\nWelcome to Epoch!')
	print('\nThe following prompts will determine the settings for a new team.')

	teams = team.get_all_teams()
	if teams is not None and len(teams) > 0:
		print('\nThe following are current teams in this integration: ')
		for t in teams:
			team_id = int(t[0])
			team_name = str(t[1])
			print('Team #' + str(team_id) + ' is \'' + str(team_name) + '\'')
		print('- End of teams -')

	team_id = raw_input('What is the ID for the team (Ex: 1)?: ')
	if team_id is None:
		team_id = 1

	team_name = raw_input('What is the name for the team (Ex: Island Clash)?: ')
	if team_name is None:
		print('Please provide a valid team name!')
		return None

	# create the team in the database
	team.create_team(team_id, team_name)

	print('Team ' + str(team_name) + ' with ID of ' + str(team_id) + ' was successfully added to Epoch!')

def handle_create_user():
	'''
	Handles the creation of a user.
	'''
	print('----- ----- ----- -----')
	print('---- User Creation ---- ')
	print('----- ----- ----- -----')
	print('\nWelcome to Epoch!')
	print('\nThe following prompts will determine the settings for a new user.')

	username = raw_input('What is the Slack username for this user (Ex: stephen)?: ')
	if username is None or len(username) < 3:
		print('Please provide a valid username!')
		return None

	# determine the UUID from their username
	uuid = get_slack_uuid(username)
	if uuid is None:
		print('Unable to find that user in the Slack integration. Are you sure they exist?')
		return None
	else:
		print('We have resolved ' + str(username) + '\'s as ' + str(uuid) + '.')

	title = raw_input('What is this user\'s title? [Engineer]: ')
	if title is None:
		title = 'Engineer'

	# show the user a list of current teams
	teams = team.get_all_teams()
	if teams is not None and len(teams) > 0:
		print('\nThe following are current teams in this integration: ')
		for t in teams:
			team_id = int(t[0])
			team_name = str(t[1])
			print('Team #' + str(team_id) + ' is \'' + str(team_name) + '\'')
		print('- End of teams -')

	team_id = raw_input('What is this user\'s team? [1]: ')
	if team_id is None:
		team_id = 1

	# OPTIONAL
	git_id = raw_input('What is this user\'s GitHub username (Ex: Unknowncmbk)?: ')

	monthly_hours = raw_input('What is the expected monthly hours for this user? [160]: ')
	if monthly_hours is None:
		monthly_hours = 160
	
	# create the user
	user.create_user(uuid, username, title, team_id, git_id, monthly_hours)
	user_session.create_user_session(uuid)

	print('User ' + str(username) + ' was successfully added to Epoch!')


# if ran from command line
if __name__ == '__main__':

	if len(sys.argv) > 1:
		cmd = sys.argv[1].lower()

		if cmd == 'help':
			print('This module is invoked in the following ways: \n')
			print('python create.py help')
			print('- Display this message.\n')
			print('python create.py list')
			print('- List users in Slack channel that do not yet have an account.\n')
			print('python create.py team')
			print('- Invoke main creation module for teams.\n')
			print('python create.py user')
			print('- Invoke main creation module for users.\n')

		elif cmd == 'list':
			users = get_not_yet_registered()

			if users is not None and len(users) > 0:
				print('The following users do not yet have an account: ')
				print('(Name, id)')
				for uuid, username in users:
					print((str(username), str(uuid))) 
			else:
				print('All users that belong to this Slack integration are registered with Epoch.')

		elif cmd == 'user':
			handle_create_user()

		elif cmd == 'team':
			handle_create_team()