#!/usr/bin/python

# local imports
from server import slack_handle
from server import git_handle
from settings import settings

# python modules
# We need to import request to access the details of the POST request
# and render_template, to render our templates (form and response)
# we'll use url_for to get some URLs for the app on the templates
from flask import Flask, request, Response
import json
import time
import logging, logging.handlers
import hmac
import hashlib

# File that the results of this script writes to
LOG_FILENAME = 'server_applet.log'
# construct logger
LOG = logging.getLogger('server_applet_log')
LOG.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, backupCount=5)
LOG.addHandler(handler)

app = Flask('Epoch')

# outgoing webhook key specified by Slack
SLACK_WEBHOOK_OUTGOING = settings.getSettings().slack_webhook
# outgoing webhook key specified by Github
GITHUB_WEBHOOK_OUTGOING = settings.getSettings().github_webhook

@app.route('/services/slack', methods=['POST'])
def handle_slack_post():
    '''
    Serves Slack's POST requests to this applet.
    '''
    # TODO add try/catch here
    # TODO add access log
    
    # get the post request form
    data_form = request.form
    if data_form is not None:

        # let's confirm that this is a slack request
        if 'token' in data_form:
            token = str(data_form['token'])

            if token == SLACK_WEBHOOK_OUTGOING:
                return slack_handle.parse_request(data_form)
            else:
                return Response('You are not authorized.'), 404
        else:
            return Response('Malformed data request.'), 400
    else:
        return Response('Malformed data request.'), 400

@app.route('/services/git', methods=['POST'])
def handle_git_post():
    '''
    Serves Github's POST requests to this applet.
    '''
    # TODO add access log

    # load the header data
    header_data = request.headers

    # whether or not this is a verified request
    verified_req = False

    # the headers should be of type `werkzeug.datastructures.EnvironHeaders`
    if header_data.has_key('X-Hub-Signature'): 
        # payload signature
        payload_sig = str(header_data.get('X-Hub-Signature'))

        # our signature
        hmac_obj = hmac.new(GITHUB_WEBHOOK_OUTGOING, request.data, hashlib.sha1)
        signature = 'sha1=' + hmac_obj.hexdigest()
        
        # because we run python 2.6, this is insecure
        verified_req = payload_sig == signature

    if not verified_req:
        return Response('Not authorized'), 400

    # git sends payload in the data section
    data = request.data
    if data is not None:
        json_data = json.loads(data)
        return git_handle.parse_request(json_data)
    else:
        return Response('Malformed data request.'), 400


    return Response('Okay.'), 200

if __name__ == "__main__":
    app.run(debug = True)