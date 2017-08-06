#!/usr/bin/python

# local modules
from settings import settings

# python modules
import MySQLdb

class Team(object):
    def __init__(self, team_id, name):
        self.team_id = int(team_id)
        self.name = str(name)

    def __str__(self):
        return 'team_id=' + str(self.team_id) + ", name=" + str(self.name)

def create_team(team_id, team_name):
    '''
    Creates the team in the database.

    Args:
        team_id: The ID of the team
        team_name: The name of the team
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''INSERT INTO team (id, name) VALUES (%s, %s);'''
    data = (int(team_id), str(team_name))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

def get_all_teams():
    '''
    Get a list of all the current teams.

    Returns:
        A list of all the current teams in the form of (team_id, team_name).
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT id, name FROM team;'''
    cur.execute(query)

    teams = []
    for tup in cur:
        team_id = int(tup[0])
        team_name = str(tup[1])

        team_obj = (team_id, team_name)
        teams.append(team_obj)

    # commit query
    db.commit()
    cur.close()

    return teams

def set_user_team(uuid, team):
    '''
    Sets the user to the specified team.

    Args:
        uuid: The uuid of the user to set
        team: The team to set the user to
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''UPDATE user SET team=%s WHERE uuid=%s;'''
    data = (int(team), str(uuid))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()
