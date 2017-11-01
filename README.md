# Epoch Time Tracker
A Python implementation of a time tracker for employees. Specifically, this software allows users to change between states, and monitor their respective sessions. Users are allowed to swap in and out of states, as well as starting/ending multiple sessions every day. 

Optionally, Github integrations can be set up and track user commits, which are posted when a user logs out.

Below is an image of the integration into Slack:
![alt text](https://github.com/Unknowncmbk/epoch-time-tracker/blob/master/images/login.png "User Logging In")

Below is an image of logging out of Slack:
![alt text](https://github.com/Unknowncmbk/epoch-time-tracker/blob/master/images/timestamp_developer.png "User Logging Out")

## Requirements
- [Python](https://www.python.org/download/releases/2.6/): Version 2.6 or higher.
- [Flask](http://flask.pocoo.org): To serve as the backend 'server' handler.
- [Ngrok](https://ngrok.com): To expose localhost SSL.
- [MariaDB](https://mariadb.org): or MySQL as the DBMS.

## External Software Hooks
- [Slack](https://api.slack.com): Integrations setup to handle slash commands and reply to custom channels.
- [Github](https://developer.github.com): Integrations to listen to commit changes and log them.

## Installation
Note: This project was compiled on CentOS 6.

You'll need to install the [required modules](https://github.com/Unknowncmbk/epoch-time-tracker/blob/master/setup/install.txt) using a package installer. If you are not using CentOS 6, look for alternatives modules. 

You'll need to run the [schema table](https://github.com/Unknowncmbk/epoch-time-tracker/blob/master/setup/database/database_schema.txt) in order to populate the database with the correct information. Do not forget to create a new database!

## Settings
Fill out the appropriate settings in [settings.txt](https://github.com/Unknowncmbk/epoch-time-tracker/blob/master/epoch/settings/settings.txt).

Database Credentials:
- `Host/Database/User/Pass` for a MySQL server.

General Settings:
- `company_name`: The name of your company.
- `company_url`: The URL to your company's website.
- `company_icon_url`: The URL to an icon that represents your company logo.

Flask Settings:
- `host_ip`: The IP of the machine you are running this on. If you use localhost, POST payloads might not reach the application, so use the hard IP.
- `port`: The port number to run flask on. 

Slack Settings:
- `api_token`: Your app's xoxp- token (available on the Install App page)
- `api_url`: The webhook URL that you copied off the Incoming Webhook page
- `webhook_outgoing`: Your app's Verification Token (available on the Basic Information page)

Github Settings:
- `webhook_outgoing`: Your custom verification token that you use in your project's Settings/Webhooks file.

## Setup
Setup a screen session to run ngrok, to expose localhost bindings. This is to allow SSL connections to Flask.

Create a directory to hold the module, and populate the contents with this project.
```
mkdir /home/epoch
```

You'll have to create a file that holds the login details, under `epoch/settings/` called `settings.txt`.

Setup a screen session to handle the server application and run it:
```
screen -S server_app
cd /home/epoch
python server_applet.py
```

Setup another screen session to handle the pulse of Epoch, a file that is a repeating task to credit users with working:
```
screen -S pulse
cd /home/epoch
python pulse.py
```
Note: If you need to stop pulse, delete `pulse.pid`.

## Post Setup
You'll want to setup the Slack integrations to call your custom URL (ngrok). Below are example URLs that could be resolved based off `ngrok`, and you'll use this as custom integration into this service:

```
Webhook for Slack posts:
https://example.com/services/slack
```
The above url should be called with your `outgoing Slack webhook token`.

```
Webhook for GitHub posts:
https://example.com/services/git
```
The above url should be called with your `outgoing GitHub webhook token`.

## Additional Modules

### Clean Start
If you ever need to clean Epoch, due to maintenance, you can force log out users when you restart Epoch using:
```
python pulse.py CLEAN
```

### User Creation
You can create users and teams within this module.

The following are commands that can be invoked with the `creation` module:

`python create.py help`
- Displays the help page

`python create.py list`
- Lists all the users in the Slack server that do not yet have an account.

`python create.py team`
- Create a team, so you can sort users.

`python create.py user`
- Create a new user.

### User Session Tracking
You can track session information for users as well as adding/removing/modifying logs that were created from Epoch.

The following are commands that can be invokved with the `tracking` module:

`python track.py help`
- Display this message.

`python track.py add`
- Add a session log/timestamp for a user.

`python track.py remove`
- Remove a session log/timestamp from a user.

`python track.py modify`
- Change a session log/timestamp's worked hours for a user.

`python track.py list`
- List the status of all users

`python track.py session`
- List session log/timestamps for a user.

`python track.py verify`
- Verify and sign timestamps for a user.

`python track.py report`
- Generate session reports for a user, and send it to them!
