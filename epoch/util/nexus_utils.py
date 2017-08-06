#!/usr/bin/python

# local imports

# python modules
import os

def get_pid(file_name):
    '''
    Args:
        file_name: The name of the pid file
    Returns:
        True if the file exists, False otherwise.
    '''
    return os.path.isfile(file_name)

def delete_pid(file_name):
    '''
    Args:
        file_name: The name of the pid file
    Returns:
        Deletes the pid file if one exists.
    '''
    if get_pid(file_name):
        os.remove(file_name)

def create_pid(file_name):
    '''
    Args:
        file_name: The name of the pid file
    Returns:
        Creates the pid file if one does not exist.
    '''
    if not get_pid(file_name):
        f = open(file_name, 'w')
        f.write('running=true');
        f.close()