#!/usr/bin/python

# local modules
from util import slack_api

# python modules
import json
import socket
import MySQLdb

class Settings(object):
    def __init__(self, host_ip, db_host, db_user, db_pass, db_name, company_name, company_url, company_icon, flask_ip, flask_port, slack_api_token, slack_api_url, slack_webhook, github_webhook):
        self.host_ip = host_ip

        # MySQL creds
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name

        self.db_cxn = MySQLdb.connect(host=self.db_host, user=self.db_user, passwd=self.db_pass, db=self.db_name)
        
        # general settings
        self.company_name = company_name
        self.company_url = company_url
        self.company_icon = company_icon

        # flask settings
        self.flask_ip = flask_ip
        self.flask_port = flask_port

        # slack api post settings
        self.slack_api_token = slack_api_token
        self.slack_api_url = slack_api_url

        # external webhooks
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
#host_ip = socket.gethostbyname(socket.getfqdn())
host_ip = socket.getfqdn()

# construct settings object
settings = Settings(host_ip=host_ip, db_host=s['database_creds']['host'], db_user=s['database_creds']['user'], db_pass=s['database_creds']['pass'], db_name=s['database_creds']['database'], company_name=s['general_settings']['company_name'], company_url=s['general_settings']['company_url'], company_icon=s['general_settings']['company_icon_url'], flask_ip=s['flask_settings']['host_ip'], flask_port=s['flask_settings']['port'], slack_api_token=s['slack_settings']['api_token'], slack_api_url=s['slack_settings']['api_url'], slack_webhook=s['slack_settings']['webhook_outgoing'], github_webhook=s['github_settings']['webhook_outgoing'])

# configure a Slack server in order to send messages TO Slack
slack_api_url = settings.slack_api_url
slack_headers = {'content-type': 'application/json'}
slack_server = slack_api.SlackAPI(api_url=slack_api_url, headers=slack_headers)

def getSettings():
    '''
    Returns:
        The construct settings object.
    '''
    return settings

def getSlack():
    '''
    Returns:
        The slack server instance.
    '''
    return slack_server

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