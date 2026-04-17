import subprocess
import time

while True:
    # Run the command
    subprocess.run(['./Run.sh', '-m', 'xor_scnm', '-s', '40', '-x', 'a'])

    # Optional: Wait a moment before restarting the command
    time.sleep(1)
