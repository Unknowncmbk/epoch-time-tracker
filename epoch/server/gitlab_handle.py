#!/usr/bin/env python

# local modules
from component import repo
from component import user
from component import user_session
from settings import settings

# python modules
from flask import Response

def parse_request(data_form):
	'''
	Parses the request using the specified data_form.

	Args:
		data_form: The data form from the request

	Returns:
		A response object based off of how the request was parsed.
	'''

	# TODO: add try/except here

	# if exists, in the form of (proj_id, proj_name)
	proj_info = _filter_project(data_form)
	if proj_info is not None:
		proj_id, proj_name = proj_info

		# create repo info in database if doesn't exist
		if not repo.repo_exists(proj_id, proj_name):
			repo.set_repo(proj_id, proj_name)

		# if exists in the form of (sender_id, sender_name)
		sender_info = _filter_sender(data_form)
		if sender_info is not None:
			sender_id, sender_name = sender_info

			# make sure git info for this user is set in DB
			repo.check_git_user(sender_id, sender_name)
			
			# check their state, to notify them that they might be offline
			slack_uuid = repo.get_slack_uuid(sender_id, sender_name)
			if slack_uuid is not None:
				user_state = user_session.get_state(slack_uuid)
				if user_state == 'OFFLINE':
					# send slack message to channel
					settings.getSlack().send_message(contents='I see you sent a commit for the ' + str(proj_name) + ' repository. You know you are OFFLINE with Epoch right?', channel=str(slack_uuid), username='Epoch Bot', icon_emoji=':loudspeaker:')

			if 'commits' in data_form:
				commit_data = data_form['commits']

				# for each commit
				for c in commit_data:
					message_data = str(c['message'].encode('ascii', 'ignore'))
					commit_url = str(c['url'])

					repo.create_commit_log(repo_id=proj_id, user_id=slack_uuid, commit_text=message_data, commit_url=commit_url)
					
	return Response('Okay'), 200

def _filter_project(data_form):
	'''
	Filters out the project information for this POST request handle.

	Args:
		data_form: The data form from the request

	Returns:
		The project information in the form of (proj_id, proj_name), 
		if it exists, otherwise None.
	'''

	if data_form is not None:
		if 'project' in data_form:
			proj_data = data_form['project']

			if proj_data is not None:
				proj_id = int(proj_data['id'])
				proj_name = str(proj_data['name'])
				return (proj_id, proj_name)

	return None

def _filter_sender(data_form):
	'''
	Filters out the sender information for this POST request handle.

	Args:
		data_form: The data form from the request

	Returns:
		The sender information in the form of (sender_id, sender_name), 
		if it exists, otherwise None.
	'''

	if data_form is not None:
		if 'user_id' in data_form:
			if 'user_username' in data_form:
				sender_id = int(data_form['user_id'])
				sender_name = str(data_form['user_username'])

				return (sender_id, sender_name)

	return None
