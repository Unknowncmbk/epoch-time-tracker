#!/usr/bin/python

# local modules
from settings import settings

# python modules
import MySQLdb

def repo_exists(repo_id, repo_name):
    '''
    Get whether or not the repo already exists in the database.

    Args:
        repo_id: The ID of the repository
        repo_name: The name of the repository

    Returns:
        True if the repo exists, False otherwise.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT id FROM dev_repo WHERE id=%s and name=%s;'''
    data = (int(repo_id), str(repo_name))
    cur.execute(query, data)

    exists = False

    for tup in cur:
        result = tup[0]
        if result is not None:
            result = int(tup[0])
            if result == repo_id:
                exists = True

    # commit query
    db.commit()
    cur.close()

    return exists

def set_repo(repo_id, repo_name):
    '''
    Sets the specified repo in the database. Updates the repo name if it changed.

    Args:
        repo_id: The ID of the repository
        repo_name: The name of the repository

    Returns:
        True if the repo was set, False if something happened.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''INSERT IGNORE INTO dev_repo (id, name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name=VALUES(name);'''
    data = (int(repo_id), str(repo_name))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

    return True

def check_git_user(user_id, username):
    '''
    Sets the specified git user in the database. Updates the record if it changed.

    Args:
        user_id: The ID of the user
        username: The name of the user

    Returns:
        True if the user was set, False if something happened.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''INSERT IGNORE INTO git_user (id, name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name=VALUES(name);'''
    data = (int(user_id), str(username))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

    return True

def get_slack_uuid(user_id, username):
    '''
    Get the Slack uuid for the specified github user_id and username.

    Specifically, this allows us to see their github credentials.

    Args:
        user_id: The ID of the user
        username: The name of the user

    Returns:
        The UUID of the user for their slack account if it exists, else None.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT U.uuid FROM user U, git_user GU WHERE U.git_id=GU.name AND GU.id=%s and GU.name=%s;'''
    data = (int(user_id), str(username))
    cur.execute(query, data)

    slack_uuid = None

    for tup in cur:
        result = tup[0]
        if result is not None:
            slack_uuid = str(result)

    # commit query
    db.commit()
    cur.close()

    return slack_uuid

def get_git_uuid(slack_id):
    '''
    Get the git id for the specified slack user.

    Args:
        slack_id: The UUID for the slack user

    Returns:
        The id of the user for their git account if it exists, else None.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT GU.id FROM git_user GU, user U WHERE U.git_id=GU.name AND U.uuid=%s;'''
    cur.execute(query, str(slack_id))

    git_uuid = None

    for tup in cur:
        result = tup[0]
        if result is not None:
            git_uuid = int(result)

    # commit query
    db.commit()
    cur.close()

    return git_uuid

def create_commit_log(repo_id, user_id, commit_text, commit_url):
    '''
    Inserts into the database the commit as a log.

    Args:
        repo_id: The ID of the repository
        user_id: The id of the user that did the commit
        commit_text: The text that was in the commit
        commit_url: The URL for more information on the commit

    Returns:
        True if the commit log was successfully created, False if something happened.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''INSERT INTO log_dev_commit (repo_id, user_id, message, url) VALUES (%s, %s, %s, %s);'''
    data = (int(repo_id), int(user_id), str(commit_text), str(commit_url))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

    return True

def get_all_commit_logs(slack_id):
    '''
    Get all the commit logs that this slack user has.

    Args:
        slack_id: The user's slack ID
    Returns:
        A list of data in the form of (repo_name, commit_text, commit_url).
    '''

    result = []

    git_id = get_git_uuid(slack_id)
    if git_id is not None:
        # Get new database instance
        db = settings.getDatabase()

        cur = db.cursor()
        query = '''SELECT DR.name, LDC.message, LDC.url FROM dev_repo DR, log_dev_commit LDC WHERE LDC.user_id=%s AND LDC.repo_id=DR.id ORDER BY LDC.creation DESC;'''
        cur.execute(query, int(git_id))

        for tup in cur:
            repo_name = str(tup[0])
            commit_text = str(tup[1])
            commit_url = str(tup[2])

            data = (repo_name, commit_text, commit_url)
            result.append(data)

        # commit query
        db.commit()
        cur.close()

    return result

def get_commit_logs(slack_id, start_date, end_date):
    '''
    Get all the commit logs that this slack user has within the timeframe.

    Args:
        slack_id: The user's slack ID
        start_date: The starting date to search for 
        end_date: The end date to stop search for
    Returns:
        A list of data in the form of (repo_name, commit_text, commit_url).
    '''

    result = []

    git_id = get_git_uuid(slack_id)
    if git_id is not None:
        # Get new database instance
        db = settings.getDatabase()

        cur = db.cursor()
        query = '''SELECT DR.name, LDC.message, LDC.url FROM dev_repo DR, log_dev_commit LDC WHERE LDC.user_id=%s AND LDC.repo_id=DR.id AND (LDC.creation BETWEEN %s and %s) ORDER BY LDC.creation DESC;'''
        data = (int(git_id), str(start_date), str(end_date))
        cur.execute(query, data)

        for tup in cur:
            repo_name = str(tup[0])
            commit_text = str(tup[1])
            commit_url = str(tup[2])

            c = (repo_name, commit_text, commit_url)
            result.append(c)

        # commit query
        db.commit()
        cur.close()

    return result


