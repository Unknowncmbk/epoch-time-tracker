#!/usr/bin/python

# local imports
from component import user
from component import user_session
from settings import settings
from util import nexus_utils
from util import slack_api

# python modules
import MySQLdb
from threading import Thread
import threading
import time
import sys
import logging, logging.handlers

# name of pid session file
PID_NAME = 'pulse.pid'

# How often Pulse operates in seconds. For example every 5 seconds add time.
WORK_INTERVAL = 5

# File that the results of this script writes to
LOG_FILENAME = 'pulse.log'
# construct logger
LOG = logging.getLogger('pulse_log')
LOG.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, backupCount=5)
LOG.addHandler(handler)

# configure a Slack server in order to send messages TO Slack
slack_server = settings.getSlack()

class Pulse(Thread):
    def __init__(self):
        super(Pulse, self).__init__()
        self.stop_flag = threading.Event()

        # settings for this module
        self.box_settings = settings.getSettings()

        # counter for checking the .pid file
        self.pid_counter = 0

        # the timestamp of the last time the credit for user sessions happened
        self.credit_event = time.time()
        self.users = {}

        # create pid file
        nexus_utils.create_pid(PID_NAME)

    def run(self):
        '''
        Runs the task.
        '''

        # loop infinitely until stopped
        while self.is_active():
            self.onInterval()
            time.sleep(1)

    def stop(self):
        '''
        Stop this task from running.
        '''
        self.stop_flag.set()

    def is_active(self):
        '''
        Returns:
            True if this task is active, False otherwise.
        '''
        return not self.stop_flag.isSet()

    def onInterval(self):
        '''
        Every interval of the task, we want to do something.
        '''
        try:
            # check if Pulse is still running
            self.check_pulse()
        except Exception as e:
            print(e)
            LOG.debug(str(time.ctime(time.time())) + ': Exception checking pulse. Error: %s' % e)

        # try:
        self.work()
        # except Exception as e:
        #     print(e)
        #     LOG.debug(str(time.ctime(time.time())) + ': Exception working. Error: %s' % e)


    def check_pulse(self):
        '''
        Read the pulse of this task.
        '''

        # increment pid counter
        self.pid_counter = self.pid_counter + 1

        if self.pid_counter > 10:
            self.pid_counter = 0

            # if no pid, stop running
            if not nexus_utils.get_pid(PID_NAME):
                print('No pid exists, stopping!')
                self.stop()

                # send slack message to channel
                slack_server.send_message(contents='Epoch\'s Pulse has stopped! It died!?', channel='#work-progress', username='Epoch Bot', icon_emoji=':boom:')

                # close db connection
                settings.getSettings().close()
                return

    def work(self):
        '''
        This pulse works, serving the users, incrementing their times.
        '''

        # get the current time
        curr_time = time.time()

        if curr_time - self.credit_event > WORK_INTERVAL:

            # amount of milliseconds to credit to everyone working
            credit_amount = int((curr_time - self.credit_event) * 1000)

            # update timestamp for last time we credited
            self.credit_event = curr_time

            # load all users from db, if they dont exist in hash yet
            self.load_users()

            for key in self.users:
                user_obj = self.users[key]

                # get the state of the user
                state = user_session.get_state(user_obj.uuid)

                if state == 'ONLINE':
                    # update in the db their work time
                    user_session.update_work_time(user_obj.uuid, credit_amount)

                    user_obj.work_time_ms = user_obj.work_time_ms + credit_amount

                    # every hour notify them of how long they've worked
                    hours_worked = int(user_obj.work_time_ms / 3600000)
                    if hours_worked >= 1:

                        # when did we last notify them about their time
                        if user_obj.notify_hour < hours_worked:
                            user_obj.notify_hour = user_obj.notify_hour + 1

                            # send slack message to channel
                            slack_server.send_message(contents='You have been working for ' + str(hours_worked) + ' hours this session.', channel='@' + str(user_obj.username), username='Epoch Bot', icon_emoji=':loudspeaker:')

                    # reset the pause time
                    user_obj.pause_time_ms = 0
                elif state == 'PAUSED':
                    user_obj.pause_time_ms = user_obj.pause_time_ms + credit_amount

                    # if 15 minutes have passed, send slack notification
                    if user_obj.pause_time_ms > 15 * 60 * 1000:
                        user_obj.pause_time_ms = 0
                        # send slack message to channel
                        slack_server.send_message(contents='You have been idle/paused for 15 minutes. When you get back please use `/epoch resume`.', channel='@' + str(user_obj.username), username='Epoch Bot', icon_emoji=':loudspeaker:')
                elif state == 'OFFLINE':
                    # reset their work time
                    user_obj.work_time_ms = 0
                    user_obj.pause_time_ms = 0

    def load_users(self):
        '''
        Loads all the users to this Pulse.
        '''
        # load all the users
        users = user.get_all_users()
        if users is not None and len(users) > 0:
            for uuid, name in users:
                # if not already loaded in, create it
                if uuid not in self.users:
                    u_obj = user.User(uuid, name)
                    self.users[uuid] = u_obj


def force_logout_users():
    '''
    Forces all the users to logout, sending them a notification.
    '''
    users = user.get_all_users()

    if users is not None and len(users) > 0:
        for uuid, username in users:

            state = user_session.get_state(uuid)
            if state != 'OFFLINE':

                print('Force logging out ' + str(username) + ' as their state was ' + str(state))
                LOG.debug(str(time.ctime(time.time())) + ': Force logging out ' + str(username) + ' as their state was ' + str(state))

                # set the new state
                user_session.set_state(uuid, 'OFFLINE')
                user.log_state_change(uuid, 'OFFLINE', state)

                # get how long they worked
                msecs = user_session.get_work_time(uuid)
                start_time = user_session.get_session_timestamp(uuid)
                end_time = time.strftime('%Y-%m-%d %H:%M:%S')

                # create the session log
                user_session.create_user_session_log(uuid, msecs, start_time, end_time)

                # reset their work time to 0
                user_session.set_work_time(uuid, 0)
                user_session.set_session_timestamp(uuid)

                # send slack message to channel
                slack_server.send_message(contents='Epoch was restarted and you were logged out. Please use `/epoch start`.', channel='@' + str(username), username='Epoch Bot', icon_emoji=':loudspeaker:')

# if ran from command line
if __name__ == '__main__':

    print('Starting Pulse... vroom vroom')
    LOG.debug(str(time.ctime(time.time())) + ': Starting Pulse...: vroom vroom')

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'CLEAN' or cmd == 'clean':
            force_logout_users()

        # send slack message to channel
    slack_server.send_message(contents='Epoch\'s Pulse has now been started!', channel='#work-progress', username='Epoch Bot', icon_emoji=':rocket:')

    # Schedule a repeating task to handle off thread instructions
    pulse = Pulse()
    pulse.start()



