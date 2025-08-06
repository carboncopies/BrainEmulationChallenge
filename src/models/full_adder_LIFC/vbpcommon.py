# Enable common components used by multiple models:
from datetime import datetime
from time import sleep
import json
import os
from sys import path
from pathlib import Path

path.insert(0, str(Path(__file__).parent.parent.parent)+'/components')

import BrainGenix.NES as NES
from NES_interfaces.KGTRecords import plot_recorded


def PlotAndStoreRecordedActivity(recording_dict:dict, savefolder:str, figspecs:dict)->bool:
    if not isinstance(recording_dict, dict):
        print('Error: Recorded activity is not a dict')
        return False
    if "StatusCode" not in recording_dict:
        print('Error: Missing StatusCode in recorded activity dict')
        return False
    try:
        assert(recording_dict["StatusCode"] == 0)
        print('Keys in activity record: '+str(list(recording_dict["Recording"].keys())))
    except Exception as e:
        print('Error: Recorded activity content not usable: '+str(e))
        return False
    try:
        plot_recorded(
            savefolder=savefolder,
            data=recording_dict["Recording"],
            figspecs=figspecs,)
    except Exception as e:
        print('Error: Failed to plot and store recorded acticity: '+str(e))
        return False
    return True

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

def AddInputToDB(DBdata:dict, inkey:str, indata):
    DBdata['entry']['IN'][inkey] = indata

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
# making a lock file. Then reads the current database and returns
# the data.
# If no database file was found returns empty data.
# If a file error occurs returns None.
# The lock file is removed if a file error occurred.
# Otherwise, the lock file is removed if keeplock is False.
def LoadExpsDB(DBdata:dict, keeplock=False)->dict:
    WaitToLockDB(DBdata)
    if not os.path.exists(DBdata['dbfile']):
        if not keeplock:
            UnlockDB(DBdata)
        return {}
    try:
        with open(DBdata['dbfile'], 'r') as f:
            DBcontent = json.load(f)
            if not keeplock:
                UnlockDB(DBdata)
            return DBcontent
    except Exception:
        UnlockDB(DBdata)
        print('Error: Unable to read experiments database file '+DBdata['dbfile'])
        return None

# Loads the current database with LoadExpsDB() and adds
# the new entry and saves the updated data to the database.
# Finally, unlocks the database file by removing the lock file.
def UpdateExpsDB(DBdata:dict)->bool:
    DBcontent = LoadExpsDB(DBdata, keeplock=True)
    if DBcontent is None:
        return False
    
    if DBdata['key'] not in DBcontent:
        DBcontent[DBdata['key']] = []

    DBcontent[DBdata['key']].append(DBdata['entry'])

    try:
        with open(DBdata['dbfile'], 'w') as f:
            json.dump(DBcontent, f, indent=2)
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

def ExitOrReturn(DBdata:dict, exit_on_error:bool, errmsg:str, returnvalue=None):
    if exit_on_error:
        ErrorExit(DBdata, errmsg)
    else:
        return returnvalue

def GetMostRecentDBEntry(DBdata:dict, key:str, modelfromIN:bool, modelname:str, exit_on_error=True)->dict:
    DBcontent = LoadExpsDB(DBdata)
    if DBcontent is None:
        return ExitOrReturn(DBdata, exit_on_error, 'Experiments database error: File read error')
    if len(DBcontent) == 0:
        return ExitOrReturn(DBdata, exit_on_error, 'Experiments database error: Database is empty')
    if key not in DBcontent:
        return ExitOrReturn(DBdata, exit_on_error, 'Experiments database error: Key %s not in database' % str(key))
    try:
        if modelfromIN:
            INorOUT = 'IN'
        else:
            INorOUT = 'OUT'
        for DBentry in reversed(DBcontent[key]):
            if DBentry[INorOUT]['modelname'] == modelname:
                return DBentry
    except Exception as e:
        return ExitOrReturn(DBdata, exit_on_error, 'Experiments database error: Database format is corrupted: '+str(e))
    return ExitOrReturn(DBdata, exit_on_error, 'Experiments database error: modelname %s not in database' % str(modelname))

def GetMostRecentDBEntryIN(DBdata:dict, key:str, modelfromIN:bool, modelname:str, exit_on_error=True)->dict:
    DBentry = GetMostRecentDBEntry(DBdata, key, modelfromIN, modelname, exit_on_error)
    if DBentry is None:
        return None
    if 'IN' not in DBentry:
        return ExitOrReturn(DBdata, exit_on_error, 'Experiments database error: Database format is corrupted: missing IN')
    return DBentry['IN']

def GetMostRecentDBEntryOUT(DBdata:dict, key:str, modelfromIN:bool, modelname:str, exit_on_error=True)->dict:
    DBentry = GetMostRecentDBEntry(DBdata, key, modelfromIN, modelname, exit_on_error)
    if DBentry is None:
        return None
    if 'OUT' not in DBentry:
        return ExitOrReturn(DBdata, exit_on_error, 'Experiments database error: Database format is corrupted: missing OUT')
    return DBentry['OUT']

def ClientFromArgs(DBdata:dict, Args):
    # Create Client Configuration For Local Simulation
    print(" -- Creating Client Configuration For Local Simulation")
    ClientCfg = NES.Client.Configuration()
    ClientCfg.Mode = NES.Client.Modes.Remote
    ClientCfg.Host = Args.Host
    ClientCfg.Port = Args.Port
    ClientCfg.UseHTTPS = Args.UseHTTPS
    ClientCfg.AuthenticationMethod = NES.Client.Authentication.Password
    ClientCfg.Username = "Admonishing"
    ClientCfg.Password = "Instruction"

    # Create Client Instance
    print(" -- Creating Client Instance")
    try:
        ClientInstance = NES.Client.Client(ClientCfg)
        if not ClientInstance.IsReady():
            ErrorExit(DBdata, 'NES.Client error: not ready')
    except Exception as e:
        ErrorExit(DBdata, 'NES.Client error: '+str(e))

    return ClientCfg, ClientInstance

def NewSimulation(DBdata:dict, ClientInstance, Name, Seed=0):
    # Create A New Simulation
    print(" -- Creating Simulation")
    SimulationCfg = NES.Simulation.Configuration()
    SimulationCfg.Name = Name
    SimulationCfg.Seed = Seed
    try:
        MySim = ClientInstance.CreateSimulation(SimulationCfg)
    except:
        ErrorExit(DBdata, 'NES error: Failed to create simulation')

    return SimulationCfg, MySim
