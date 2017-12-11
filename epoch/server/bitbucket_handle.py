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

	# if exists, in the form of (repo_id, repo_name)
	repo_info = _filter_repository(data_form)
	if repo_info is not None:
		repo_id, repo_name = repo_info

		# create repo info in database if doesn't exist
		if not repo.repo_exists(repo_id, repo_name):
			repo.set_repo(repo_id, repo_name)


		valid = False
		# filter out for only UPDATEs else merging branches is hell
		if 'refChanges' in data_form:
			ref_changes = data_form['refChanges']
			if ref_changes is not None and len(ref_changes) > 0:
				for rc in ref_changes:
					if 'type' in rc:
						change_type = str(rc['type'])
						if change_type == 'UPDATE':
							valid = True
						else:
							print('Unable to validate this payload, as the ref change type was ' + str(change_type))

		if 'changesets' in data_form and valid:
			change_sets = data_form['changesets']

			if 'values' in change_sets:
				values = change_sets['values']

				if values is not None and len(values) > 0:
					for v in values:

						# extract the toCommit
						if 'toCommit' in v:
							to_commit = v['toCommit']

							committer_data = _filter_committer(to_commit)
							# if committer exists
							if committer_data is not None:
								committer_name, committer_email = committer_data

								# check their state, to notify them that they might be offline
								slack_uuid = _get_slack_uuid(committer_email)
								if slack_uuid is not None:

									user_state = user_session.get_state(slack_uuid)
									if user_state == 'OFFLINE':
										# send slack message to channel
										settings.getSlack().send_message(contents='I see you sent a commit for the ' + str(repo_name) + ' repository. You know you are OFFLINE with Epoch right?', channel=str(slack_uuid), username='Epoch Bot', icon_emoji=':loudspeaker:')

									commit_id = to_commit['id']
									message_data = str(to_commit['message'].encode('ascii', 'ignore'))

									# find the first commit url
									commit_url = _filter_url(v)

									# create the commit log
									repo.create_commit_log(repo_id=repo_id, user_id=slack_uuid, commit_text=message_data, commit_url=commit_url)
		else:
			print('Unable to validate this payload, as the form was not valid.')
					
	return Response('Okay'), 200

def _filter_repository(data_form):
	'''
	Filters out the repository information for this POST request handle.

	Args:
		data_form: The data form from the request

	Returns:
		The repository information in the form of (repo_id, repo_name), 
		if it exists, otherwise None.
	'''

	if data_form is not None:
		if 'repository' in data_form:
			repo_data = data_form['repository']

			if repo_data is not None:
				repo_id = int(repo_data['id'])
				repo_name = str(repo_data['name'])
				return (repo_id, repo_name)

	return None

def _filter_committer(data_form):
	'''
	Filters out the committer information for this POST request handle.

	Args:
		data_form: The data form from the request

	Returns:
		The committer information in the form of (committer_name, committer_email), 
		if it exists, otherwise None.
	'''

	if data_form is not None:

		if 'committer' in data_form:
			committer_data = data_form['committer']

			if committer_data is not None:
				committer_name = str(committer_data['name'])
				committer_email = str(committer_data['emailAddress'])

				return (committer_name, committer_email)

	return None

def _filter_url(data_form):
	'''
	Filters out the URL information for this POST request handle.

	Args:
		data_form: The data form from the request

	Returns:
		The url information in the form for this post request, 
		if it exists, otherwise None.
	'''

	if data_form is not None:

		if 'links' in data_form:
			link_data = data_form['links']

			if link_data is not None:
				if 'self' in link_data:
					internal_data = link_data['self']

					if internal_data is not None and len(internal_data) > 0:
						for i in internal_data:
							if 'href' in i:
								return i['href']

	return None	

def _get_slack_uuid(bitbucket_email):
	'''
	Get the Slack UUID of the user with the specified bitbucket_email.

	Args:
		bitbucket_email: The email of the user

	Returns:
		The Slack UUID for the user, if one exists, otherwise None.
	'''
	# Get new database instance
	db = settings.getDatabase()

	cur = db.cursor()
	query = '''SELECT uuid FROM user U WHERE bitbucket_email=%s;'''
	cur.execute(query, [str(bitbucket_email)])

	slack_uuid = None

	for tup in cur:
		result = tup[0]
		if result is not None:
			slack_uuid = str(result)

	# commit query
	db.commit()
	cur.close()

	return slack_uuid