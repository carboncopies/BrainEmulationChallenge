import time
import psutil
import datetime
import threading
import os

# SOURCE OF THE CODE for display_usage:
# https://www.youtube.com/watch?v=rdxt6ntfX24

class ResourceMonitor:
    def __init__(self, output_dir=None, interval=0.5, create_plots=True):
        """
        Initializing the ResourceMonitor Object

        Args:
            output_dir: Directory to save monitoring data (typically a .txt file).
            interval: Time interval between resource checking
            create_plots: generating plots for the resource usage based off if true or false
        """

        self.interval = interval
        self.create_plots = create_plots
        self.running = False # Flag to see if monitor is running
        self.last_disk_read = 0
        self.last_disk_write = 0 
        self.thread = None # Indication to see which thread it is attached to

        self.data = {
            'timestamp': [],
            'cpu_percent': [],
            'memory_percent': [], 
            'disk_io_reads': [], 
            'disk_io_writes': []
        }

        if output_dir:
            self.output_dir = output_dir
        else:
            # Creating a default output directory if there is none provided
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            self.output_dir = f"resource_monitor_{timestamp}.txt"

    def start(self):
        """
        Starting the monitoring process
        """
        disk_io = psutil.disk_io_counters() # returns system-wide disk I/O statistics since the last system boot
        if disk_io:
            self.last_disk_read = disk_io.read_bytes
            self.last_disk_write = disk_io.write_bytes

        self.running = True
        self.thread = threading.Thread(target=self._monitor_resources)
        self.thread.daemon = True
        self.thread.start()
        print(f"Resource monitoring started. Data will be saved to {self.output_dir}")

    def stop(self):
        """
        Stopping the monitoring process and save data
        """

        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)

        print(f"\nResource monitoring stopped. Data collected: {len(self.data['timestamp'])} samples")
    
    def _monitor_resources(self):
        """
        Monitor system resources such as CPU, memory, and disk I/O.
        """

        while self.running:
            curr_time = time.time()

            # Get CPU usage
            cpu_percent = psutil.cpu_percent()
            # Get memory usage
            mem_percent = psutil.virtual_memory().percent

            # Get disk I/O usage
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_read_delta = disk_io.read_bytes - self.last_disk_read
                disk_write_delta = disk_io.write_bytes - self.last_disk_write
                self.last_disk_read = disk_io.read_bytes
                self.last_disk_write = disk_io.write_bytes
            else:
                disk_read_delta = 0
                disk_write_delta = 0

            # Append data to the dictionary
            self.data['timestamp'].append(curr_time)
            self.data['cpu_percent'].append(cpu_percent)
            self.data['memory_percent'].append(mem_percent)
            self.data['disk_io_reads'].append(disk_read_delta)
            self.data['disk_io_writes'].append(disk_write_delta)
    
            # Print the current resource usage
            print(f"\rCPU: {cpu_percent:.2f}% | MEM: {mem_percent:.2f}% | DISK READ: {disk_read_delta} bytes | DISK WRITE: {disk_write_delta} bytes", end="")   

            time.sleep(self.interval)

    # displays the cpu and memory usage
    def display_usage(cpu_usage, mem_usage, bars=50):
        cpu_percent = (cpu_usage / 100.0) 
        cpu_bar = '◾' * int(cpu_percent * bars) + '-' * (bars - int(cpu_percent * bars)) # filling in the bar

        mem_percent = (mem_usage / 100.0)
        mem_bar = '◾' * int(cpu_percent * bars) + '-' * (bars - int(cpu_percent * bars)) # filling in the bar with a color

        print(f"\rCPU Usage: |{cpu_bar}| {cpu_usage:.2f}%  ", end="")
        print(f"MEM Usage: |{mem_bar}| {mem_usage:.2f}%  ", end="\r")


# Test function to run a simple test of the ResourceMonitor
def test_resource_monitor():
    print("Testing ResourceMonitor...")
    
    # Create a monitor instance
    monitor = ResourceMonitor(output_dir="test_monitor_data")
    
    # Start monitoring
    monitor.start()
    
    # Simulate some work
    print("Simulating CPU load for 5 seconds...")
    for _ in range(5):
        # Create some CPU load
        for _ in range(1000000):
            _ = 1 + 1
        
        # Create some disk IO
        with open("test_file.txt", "w") as f:
            f.write("A" * 1000000)
        
        time.sleep(1)
    
    # Stop monitoring
    monitor.stop()
    
    # Print collected data
    print("\nData collected:")
    print(f"Timestamps: {len(monitor.data['timestamp'])}")
    print(f"CPU samples: {len(monitor.data['cpu_percent'])}")
    print(f"Memory samples: {len(monitor.data['memory_percent'])}")
    print(f"Disk read samples: {len(monitor.data['disk_io_reads'])}")
    print(f"Disk write samples: {len(monitor.data['disk_io_writes'])}")
    
    # Display some of the data
    if monitor.data['timestamp']:
        print("\nSample data:")
        for i in range(min(5, len(monitor.data['timestamp']))):
            print(f"Sample {i}: CPU={monitor.data['cpu_percent'][i]:.2f}%, "
                  f"Memory={monitor.data['memory_percent'][i]:.2f}%, "
                  f"Disk read={monitor.data['disk_io_reads'][i]}, "
                  f"Disk write={monitor.data['disk_io_writes'][i]}")
    
    # Clean up test file
    if os.path.exists("test_file.txt"):
        os.remove("test_file.txt")
    
    print("\nTest completed.")


# Call the test function 
if __name__ == "__main__":
    test_resource_monitor()