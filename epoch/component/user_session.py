#!/usr/bin/python

# local modules
from settings import settings

# python modules
import MySQLdb

def create_user_session(uuid):
    '''
    Creates a new user session in the user_session table.

    Args:
        uuid: The uuid of the user
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''INSERT INTO user_session (user_id, state, work_time) VALUES (%s, 'OFFLINE', 0);'''
    cur.execute(query, [str(uuid)])

    # commit query
    db.commit()
    cur.close()

def get_state(uuid):
    '''
    Gets the state of the user from the user_session table.

    Args:
        uuid: The uuid of the user

    Returns:
        The current state of that user.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT state FROM user_session WHERE user_id=%s;'''
    cur.execute(query, [str(uuid)])

    state = None
    for tup in cur:
        state = str(tup[0])

    # commit query
    db.commit()
    cur.close()

    return state

def set_state(uuid, state):
    '''
    Sets the state for the user in the user_session table.

    Args:
        uuid: The uuid for that user
        state: The current state that the user is in
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''UPDATE user_session SET state=%s WHERE user_id=%s;'''
    data = (state, uuid)
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

def get_work_time(uuid):
    '''
    Gets the work_time attribute from the user_session table, as milliseconds.

    Args:
        uuid: The uuid for that user

    Returns:
        The time this user has worked, in milliseconds.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT work_time FROM user_session WHERE user_id=%s;'''
    cur.execute(query, [str(uuid)])

    msecs = 0

    for tup in cur:
        msecs = int(tup[0])

    # commit query
    db.commit()
    cur.close()

    return msecs

def set_work_time(uuid, time):
    '''
    Sets the work_time attribute in the user_session table.

    Args:
        uuid: The uuid for that user
        time: The time, in msecs, to set the work time for this user
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''UPDATE user_session SET work_time=%s WHERE user_id=%s;'''
    data = (int(time), str(uuid))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

def update_work_time(uuid, incr):
    '''
    Updates the work_time attribute in the user_session table.

    Args:
        uuid: The uuid for that user
        incr: The time increment in milliseconds for that user
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''UPDATE user_session SET work_time=work_time + %s WHERE user_id=%s;'''
    data = (incr, uuid)
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

def get_session_timestamp(uuid):
    '''
    Gets the user's timestamp for this session.

    Args:
        uuid: The uuid for that user
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT updated FROM user_session WHERE user_id=%s'''
    cur.execute(query, [str(uuid)])

    result = None

    for tup in cur:
        result = tup[0]

    # commit query
    db.commit()
    cur.close()

    return result

def set_session_timestamp(uuid):
    '''
    Sets the user's timestamp for this session as now.

    Args:
        uuid: The uuid for that user
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''UPDATE user_session SET updated=CURRENT_TIMESTAMP WHERE user_id=%s'''
    cur.execute(query, [str(uuid)])

    # commit query
    db.commit()
    cur.close()

def create_user_session_log(uuid, work_time, start_time, end_time, verified=None):
    '''
    Creates a user session log in the database for this user.

    Args:
        uuid: The uuid for that user
        work_time: The amount of time, in milliseconds, for this user
        start_time: The timestamp for when this user started
        end_time: The timstamp for when this user ended
        verified: The UUID of the user that verified this user's session
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()

    if verified is None:
        query = '''INSERT INTO log_user_session (user_id, work_time, start, end) VALUES (%s, %s, %s, %s);'''
        data = (uuid, work_time, start_time, end_time)
    else:
        query = '''INSERT INTO log_user_session (user_id, work_time, start, end, approved) VALUES (%s, %s, %s, %s, %s);'''
        data = (uuid, work_time, start_time, end_time, verified)
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

def delete_user_session_log(uuid, timestamp):
    '''
    Deletes the log for the user_session that has the same month/day. Only deletes one!

    Args:
        uuid: The uuid for that user
        timestamp: The start of that users session
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''DELETE FROM log_user_session WHERE user_id=%s AND DATE(start)=%s LIMIT 1;'''
    data = (str(uuid), str(timestamp))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

def update_user_session_log(uuid, new_work_time, timestamp, verified):
    '''
    Updates the work time for the user. Only updates one!

    Args:
        uuid: The uuid for that user
        new_work_time: The amount of time in milliseconds for this user
        timestamp: The start of that users session
        verified: The UUID of the user that verified this user's session
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''UPDATE log_user_session SET work_time=%s, approved=%s WHERE user_id=%s AND DATE(start)=%s LIMIT 1;'''
    data = (int(new_work_time), str(verified), str(uuid), str(timestamp))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

def get_total_worked(uuid):
    '''
    Get the total amount of hours this user has worked THIS month.

    Args:
        uuid: The uuid of the user

    Returns:
        The number of hours, as a float, that the user worked THIS month.
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT SUM(work_time)/3600000 as hours FROM log_user_session WHERE user_id=%s AND MONTH(start) = MONTH(CURRENT_DATE()) AND YEAR(start) = YEAR(CURRENT_DATE());'''
    cur.execute(query, [str(uuid)])

    hours = 0

    for tup in cur:
        result = tup[0]
        if result is not None:
            hours = float(tup[0])

    # commit query
    db.commit()
    cur.close()

    return hours

def get_session_logs(slack_id, start_date, end_date):
    '''
    Get all the session logs that this slack user has within the timeframe.

    Args:
        slack_id: The user's slack ID
        start_date: The starting date to search for 
        end_date: The end date to stop search for
    Returns:
        A list of data in the form of (log_id, user_id, work_time, start_date, end_date, approved).
    '''

    result = []

    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT id, user_id, work_time, start, end, approved FROM log_user_session WHERE user_id=%s AND (start BETWEEN %s and %s) ORDER BY start DESC;'''
    data = (str(slack_id), str(start_date), str(end_date))
    cur.execute(query, data)

    for tup in cur:
        if tup is not None:
            log_id = int(tup[0])
            user_id = str(tup[1])
            work_time = int(tup[2])
            start = str(tup[3])
            end = str(tup[4])
            approved = str(tup[5])

            sl = (log_id, user_id, work_time, start, end, approved)
            result.append(sl)

    # commit query
    db.commit()
    cur.close()

    return result

def get_verified_session_logs(slack_id, start_date, end_date):
    '''
    Get all the verified session logs that this slack user has within the timeframe.

    Args:
        slack_id: The user's slack ID
        start_date: The starting date to search for 
        end_date: The end date to stop search for
    Returns:
        A list of data in the form of (log_id, user_id, work_time, start_date, end_date, approved).
    '''

    result = []

    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''SELECT id, user_id, work_time, start, end, approved FROM log_user_session WHERE user_id=%s AND verified IS NOT NULL AND (start BETWEEN %s and %s) ORDER BY start DESC;'''
    data = (str(slack_id), str(start_date), str(end_date))
    cur.execute(query, data)

    for tup in cur:
        if tup is not None:
            log_id = int(tup[0])
            user_id = str(tup[1])
            work_time = int(tup[2])
            start = str(tup[3])
            end = str(tup[4])
            approved = str(tup[5])

            sl = (log_id, user_id, work_time, start, end, approved)
            result.append(sl)

    # commit query
    db.commit()
    cur.close()

    return result

def verify_session_log(trans_id, verify_uuid):
    '''
    Verifies the session log by signing the uuid to the transaction ID.

    Args:
        trans_id: The ID of the session log
        verify_uuid: The UUID of the user verifying
    '''
    # Get new database instance
    db = settings.getDatabase()

    cur = db.cursor()
    query = '''UPDATE log_user_session SET approved=%s WHERE id=%s;'''
    data = (str(verify_uuid), int(trans_id))
    cur.execute(query, data)

    # commit query
    db.commit()
    cur.close()

