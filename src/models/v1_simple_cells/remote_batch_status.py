#!../../../venv/bin/python

import subprocess
import time
import json

def check_remote_batchrun()->bool:
    # Run a script and wait for it to finish
    result = subprocess.run(['scp', '-P', '2200', 'rkoene@pve.braingenix.org:src/BrainEmulationChallenge/src/models/autoassociative/batch_state.json', './'], capture_output=True, text=True)
    # Print output and errors
    #print("Output:", result.stdout)
    #print("Errors:", result.stderr)
    return result.returncode == 0

if __name__ == '__main__':
    while True:
        success = check_remote_batchrun()
        if not success:
            print('Failed to retrieve remote batch state!')
        else:
            try:
                with open('batch_state.json', 'r') as f:
                    state = json.load(f)
                if not state['isrunning']:
                    print('==> Remote Batch Run stopped!')
                    exit(0)
                else:
                    print('Running: %d/%d' % (state['remaining'], state['total']))
            except:
                print('Failed to open batch_state.json!')
        time.sleep(60)
