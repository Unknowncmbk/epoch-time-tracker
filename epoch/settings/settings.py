#!/usr/bin/python

# python modules
import json
import socket
import MySQLdb

class Settings(object):
    def __init__(self, host_ip, db_host, db_user, db_pass, db_name, slack_api_token, slack_api_url, slack_webhook, github_webhook):
        self.host_ip = host_ip

        # MySQL creds
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name

        self.db_cxn = MySQLdb.connect(host=self.db_host, user=self.db_user, passwd=self.db_pass, db=self.db_name)
        self.slack_api_token = slack_api_token
        self.slack_api_url = slack_api_url
        self.slack_webhook = slack_webhook
        self.github_webhook = github_webhook

    def __str__(self):
        return 'host_ip: ' + str(self.host_ip) + ', db_host: ' + str(self.db_host) + ', db_user: ' + str(self.db_user) + ', db_pass: ' + str(self.db_pass) + ', db_name: ' + str(self.db_name)

    def close(self):
        '''
        Closes the DB connection
        '''
        try:
            self.db_cxn.close()
        except Exception as e:
            print ('Unable to close DB connection ' % e)


# read file for settings
json_data=open('./settings/settings.txt').read()
data = json.loads(json_data)
s = data

# ip of this machine
host_ip = socket.gethostbyname(socket.gethostname())

# construct settings object
settings = Settings(host_ip=host_ip, db_host=s['database_creds']['host'], db_user=s['database_creds']['user'], db_pass=s['database_creds']['pass'], db_name=s['database_creds']['database'], slack_api_token=s['slack_settings']['api_token'], slack_api_token=s['slack_settings']['api_url'], slack_webhook=s['slack_settings']['webhook_outgoing'], github_webhook=s['github_settings']['webhook_outgoing'])

def getSettings():
    '''
    Returns:
        The construct settings object.
    '''
    return settings

def getDatabase():
    '''
    Returns: 
        The database connection.
    '''

    try:
        getSettings().db_cxn.ping(True)
        return getSettings().db_cxn
    except Exception as e:
        print(e)
        print ('Unable to grab DB connection. Retrying... ')

        try:
            settings = Settings(host_ip, s['database_creds']['host'], s['database_creds']['user'], s['database_creds']['pass'], s['database_creds']['database'])
            return getSettings().db_cxn
        except Exception as e:
            print(e)
            print ('Unable to reopen connection.')