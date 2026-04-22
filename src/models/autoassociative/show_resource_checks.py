#!../../../venv/bin/python

# This prints resource_checks.py in a presentable manner.

import json

with open('resource_checks.json', 'r') as f:
    rc = json.load(f)

print('Client instance creation times:')
for T_Client_str in rc['T_Client']:
    print('  %s' % T_Client_str)

print('Successful API calls --')
print('Low RAM checks        : %d' % rc['low_checked'])
print('Launch RAM checks     : %d' % rc['launch_checked'])
print('Sim Deletes           : %d' % rc['delete'])
print('Sim Creates           : %d' % rc['create'])
print('GetConnectome         : %d' % rc['getconn'])
print('GetAbstractConnectome : %d' % rc['getabsconn'])
print('ModelSave             : %d' % rc['modelsave'])
print('Netmorph launches     : %d' % rc['launch'])
print('Netmorph status checks: %d' % rc['netmorphstatus'])
print('')

print('Total number of failures     : %d' % rc['failed_total'])
print('Failed Low RAM checks        : %d' % rc['low_checked_failed'])
print('Failed Launch RAM checks     : %d' % rc['launch_checked_failed'])
print('Failed Sim Deletes           : %d' % rc['delete_failed'])
print('Failed Sim Creates           : %d' % rc['create_failed'])
print('Failed GetConnectome         : %d' % rc['getconn_failed'])
print('Failed GetAbstractConnectome : %d' % rc['getabsconn_failed'])
print('Failed ModelSave             : %d' % rc['modelsave_failed'])
print('Failed Netmorph launches     : %d' % rc['launch_failed'])
print('Failed Netmorph status checks: %d' % rc['netmorphstatus_failed'])
print('')

for failure in rc['failures']:
    print('%s (RAM free: %s) incident: %s' % (failure['T'], failure['OSRAMfree'], failure['action']))
    print('\t%s' % failure['info'])
    print('')
