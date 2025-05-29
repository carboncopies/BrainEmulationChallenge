import time
import psutil
import datetime
import threading
import os
import json
import argparse
import subprocess
import signal

class ResourceMonitor:
    def __init__(self, output_dir=None, interval=0.5):
        """
        Initializing the ResourceMonitor Object

        Args:
            output_dir: Directory to save monitoring data
            interval: Time interval between resource checks
        """
        self.interval = interval
        self.running = False
        self.last_disk_read = 0
        self.last_disk_write = 0
        self.last_disk_read_count = 0
        self.last_disk_write_count = 0
        self.thread = None

        self.data = {
            'timestamp': [],
            'cpu_percent': [],
            'memory_percent': [], 
            'disk_io_read_bytes': [],
            'disk_io_write_bytes': [],
            'disk_io_read_ops': [],
            'disk_io_write_ops': []
        }

        if output_dir:
            self.output_dir = output_dir
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            self.output_dir = f"resource_monitor_{timestamp}"

    def start(self):
        """Start the monitoring process"""
        disk_io = psutil.disk_io_counters()
        if disk_io:
            self.last_disk_read = disk_io.read_bytes
            self.last_disk_write = disk_io.write_bytes
            self.last_disk_read_count = disk_io.read_count
            self.last_disk_write_count = disk_io.write_count

        self.running = True
        self.thread = threading.Thread(target=self._monitor_resources)
        self.thread.daemon = True
        self.thread.start()
        print(f"Resource monitoring started. Data will be saved to {self.output_dir}")

    def stop(self):
        """Stop monitoring and save data"""
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)

        print(f"\nWriting data to {self.output_dir}/data.json")
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except:
            pass
        with open(os.path.join(self.output_dir, "data.json"), 'w') as f:
            json.dump(self.data, f, indent=4)
        print(f"Resource monitoring stopped. Collected {len(self.data['timestamp'])} samples")
    
    def _monitor_resources(self):
        """Monitor system resources including disk IOPs"""
        while self.running:
            curr_time = time.time()

            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent()
            mem_percent = psutil.virtual_memory().percent

            # Get disk I/O usage
            disk_io = psutil.disk_io_counters()
            if disk_io:
                # Calculate byte deltas
                read_bytes_delta = disk_io.read_bytes - self.last_disk_read
                write_bytes_delta = disk_io.write_bytes - self.last_disk_write
                
                # Calculate IOPs (operation count deltas)
                read_ops_delta = disk_io.read_count - self.last_disk_read_count
                write_ops_delta = disk_io.write_count - self.last_disk_write_count
                
                # Update last values
                self.last_disk_read = disk_io.read_bytes
                self.last_disk_write = disk_io.write_bytes
                self.last_disk_read_count = disk_io.read_count
                self.last_disk_write_count = disk_io.write_count
            else:
                read_bytes_delta = 0
                write_bytes_delta = 0
                read_ops_delta = 0
                write_ops_delta = 0

            # Append data to dictionary
            self.data['timestamp'].append(curr_time)
            self.data['cpu_percent'].append(cpu_percent)
            self.data['memory_percent'].append(mem_percent)
            self.data['disk_io_read_bytes'].append(read_bytes_delta)
            self.data['disk_io_write_bytes'].append(write_bytes_delta)
            self.data['disk_io_read_ops'].append(read_ops_delta)
            self.data['disk_io_write_ops'].append(write_ops_delta)
    
            # Print current resource usage
            print(f"\rCPU: {cpu_percent:5.1f}% | MEM: {mem_percent:5.1f}% | "
                  f"R-IO: {read_ops_delta:4d} ops | W-IO: {write_ops_delta:4d} ops | "
                  f"R: {read_bytes_delta:6d} B | W: {write_bytes_delta:6d} B", end="")   

            time.sleep(self.interval)

def main():
    parser = argparse.ArgumentParser(description='Profile NES binary resource usage')
    parser.add_argument('nes_binary', type=str, help='Path to NES binary executable')
    parser.add_argument('--output', type=str, default=None, help='Output directory for monitoring data')
    parser.add_argument('--interval', type=float, default=0.5, help='Monitoring interval in seconds')
    args = parser.parse_args()

    # Create resource monitor
    monitor = ResourceMonitor(output_dir=args.output, interval=args.interval)
    
    # Assuming args.nes_binary contains the full path to the binary
    print(f"Starting NES binary: {args.nes_binary}")

    try:
        # Split the path to remove the binary file itself
        binary_dir = os.path.dirname(args.nes_binary)

        # Change the working directory to the directory containing the binary
        os.chdir(binary_dir)

        # Extract the binary name
        binary_name = os.path.basename(args.nes_binary)

        # Launch the binary in its working directory
        process = subprocess.Popen([f"./{binary_name}"])

    except Exception as e:
        print(f"Error launching binary: {e}")

    # Start monitoring
    monitor.start()
    
    try:
        # Wait for process to complete
        while process.poll() is None:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Stopping...")
    finally:
        # Cleanup process
        if process.poll() is None:
            print("Terminating NES binary...")
            process.terminate()
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
        
        # Stop monitoring
        monitor.stop()

if __name__ == "__main__":
    main()