#!/usr/bin/python

# local modules
from settings import settings
from component import user_session

# python modules
import MySQLdb
import calendar
import datetime

class User(object):
    def __init__(self, uuid, username):
        self.uuid = str(uuid)
        self.username = str(username)
        self.work_time = 0
        self.pause_time = 0

    def __str__(self):
        return 'uuid=' + str(self.uuid) + ", username=" + str(self.username)

def create_user(uuid, username, title, team, git_id, bitbucket_email, monthly_hours):
    '''
    Creates the user in the database.

    Args:
        uuid: The slack uuid for this user
        username: The slack username for this user
        title: The title for this user, or their role
        team: The team ID that this user belongs to
        git_id: The github username
        bitbucket_email: The email for the user's bitbucket
        monthly_hours: How many monthly hours this user is assigned
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''INSERT INTO user (uuid, username, title, team, git_id, bitbucket_email, monthly_hours) VALUES (%s, %s, %s, %s, %s, %s, %s);'''
    data = (str(uuid), str(username), str(title), int(team), str(git_id), str(bitbucket_email), int(monthly_hours))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

def exists(uuid):
    '''
    Args:
        uuid: The uuid for the user

    Returns:
        True if the user exists in the database, False otherwise.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT COUNT(*) FROM user WHERE uuid=%s;'''
    cur.execute(query, [str(uuid)])

    valid = False
    for tup in cur:

        count = int(tup[0])
        if count > 0:
            valid = True
            break

    # commit query
    db.commit()
    cur.close()

    return valid

def get_user(username):
    '''
    Get the user information for the specified user.

    Args:
        username: The name of the user

    Returns:
        A tuple representation of the user in the form of (uuid, username, title, team, git_id, monthly_hours).
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT uuid, username, title, team, git_id, bitbucket_email, monthly_hours FROM user WHERE username=%s;'''
    cur.execute(query, str(username))

    user_data = None

    for tup in cur:
        if tup is not None:
            uuid = str(tup[0])
            name = str(tup[1])
            title = str(tup[2])
            team_id = int(tup[3])
            git_id = str(tup[4])
            bitbucket_email = str(tup[5])
            monthly_hours = int(tup[6])
            user_data = (uuid, name, title, team_id, git_id, bitbucket_email, monthly_hours)

    # commit query
    db.commit()
    cur.close()

    return user_data

def log_state_change(uuid, state, prev_state):
    '''
    Args:
        uuid: The uuid for that user
        state: The current state that the user is in
        prev_state: The previous state for the user
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''INSERT INTO log_user_state (user_id, state, prev_state) VALUES (%s, %s, %s);'''
    data = (str(uuid), str(state), str(prev_state))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

def get_all_users():
    '''
    Returns:
        A list of user information in the database in the form of (uuid, name).
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT uuid, username FROM user;'''
    cur.execute(query)

    users = []

    for tup in cur:
        uuid = str(tup[0])
        name = str(tup[1])

        user_pair = (uuid, name)
        users.append(user_pair)

    # commit query
    db.commit()
    cur.close()

    return users

def get_goal_total(uuid):
    '''
    Get the total amount of hours this user should work in one month.

    Args:
        uuid: The uuid of the user

    Returns:
        The number of hours, as a float, that the user should work in one month.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT monthly_hours FROM user WHERE uuid=%s;'''
    cur.execute(query, str(uuid))

    hours = 0

    for tup in cur:
        hours = int(tup[0])

    # commit query
    db.commit()
    cur.close()

    return hours

def determine_goal_hours_today(uuid):
    '''
    Determines the goal hours for today.

    Args:
        uuid: The uuid of the user

    Returns:
        The number of hours, as a string, that the user should try and work today.
    '''
    
    current = user_session.get_total_worked(uuid)
    goal = get_goal_total(uuid)

    number_left = goal - current
    if number_left > 0:

        # get the int representation of today
        current_day = datetime.datetime.today().day

        # determine the days in THIS month
        now = datetime.datetime.now()
        days_in_month = calendar.monthrange(now.year, now.month)[1]

        days_left = days_in_month - current_day

        if days_left <= 0:
            if number_left > 24:
                return '>24'
            else:
                return '%.2f' % number_left
        else:
            goal = number_left / days_left
            return '%.2f' % goal

    return 'Goal Reached!'

