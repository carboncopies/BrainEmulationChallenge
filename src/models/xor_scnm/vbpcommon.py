# Enable common components used by multiple models:
from datetime import datetime
from time import sleep
import json
import os
from sys import path
from pathlib import Path

path.insert(0, str(Path(__file__).parent.parent.parent)+'/components')

def InitExpDB(_ExpsDB:str, _DBkey:str, _scriptversion:str, _initIN:dict, _initOUT:dict)->dict:
    _initIN['scriptversion'] = _DBkey+'-'+_scriptversion,
    _initIN['datetime'] = datetime.now().strftime('%Y%m%d%H%M%S'),
    return {
        'dbfile': _ExpsDB,
        'key': _DBkey,
        'entry': {
            'IN': _initIN,
            'OUT': _initOUT,
        }
    }

def AddOutputToDB(DBdata:dict, outkey:str, outdata):
    DBdata['entry']['OUT'][outkey] = outdata

def UnlockDB(DBdata:dict)->bool:
    lockfile = DBdata['dbfile']+'.locked'
    if os.path.exists(lockfile):
        os.remove(lockfile)
        return True
    return False

def WaitToLockDB(DBdata:dict)->bool:
    lockfile = DBdata['dbfile']+'.locked'
    counts = 20
    while os.path.exists(lockfile):
        sleep(0.1)
        counts -= 1
        if counts == 0:
            return False
    try:
        with open(lockfile, 'w') as f:
            f.write('Locked by %s at %s' % (DBdata['key'], DBdata['entry']['IN']['datetime']))
    except:
        return False
    return True

# Waits until no one else is using the experiments database file
# by checking if a lock file is present. Then, locks access by
# making a lock file. Then reads the current database and adds
# the new entry and saves the updated data to the database.
# Finally, unlocks the database file by removing the lock file.
def UpdateExpsDB(DBdata:dict)->bool:
    WaitToLockDB(DBdata)
    if os.path.exists(DBdata['dbfile']):
        try:
            with open(DBdata['dbfile'], 'r') as f:
                DBcontent = json.load(f)
        except Exception as e:
            UnlockDB(DBdata)
            print('Error: Unable to read experiments database file '+DBdata['dbfile'])
            return False
    else:
        DBcontent = {}
    
    if DBdata['key'] not in DBcontent:
        DBdata['key'] = []

    DBcontent[DBdata['key']].append(DBdata['entry'])

    try:
        with open(DBdata['dbfile'], 'w') as f:
            json.dump(DBcontent, f)
    except Exception as e:
        UnlockDB(DBdata)
        print('Error: Unable to write updated experiments database to file '+DBdata['dbfile'])
        return False
    UnlockDB(DBdata)
    return True

def ErrorToDB(DBdata:dict, errmsg:str):
    print(errmsg)
    if 'error' in DBdata['entry']['OUT']:
        errmsg = DBdata['entry']['OUT']+'\n'+errmsg
    AddOutputToDB(DBdata, 'error', errmsg)

def ErrorExit(DBdata:dict, errmsg:str):
    ErrorToDB(DBdata, errmsg)
    UpdateExpsDB(DBdata)
    exit(1)
