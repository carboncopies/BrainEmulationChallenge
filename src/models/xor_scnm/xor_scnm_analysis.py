import time
import psutil
import datetime
import threading
import os
import json
import argparse
import subprocess
import signal
import sys

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
        
        # Create an output directory if one isn't provided
        try:
            print(f"\nCreating directory: {self.output_dir}")
            os.makedirs(self.output_dir, exist_ok=True)
            print(f"Directory created or already exists.")
        except Exception as e:
            print(f"Error creating directory {self.output_dir}: {e}")
            # Fallback to current directory
            self.output_dir = "."
            print(f"Using fallback directory: {self.output_dir}")

        # Calculate and display averages
        self._calculate_and_display_averages()

        # Full path to the json file
        json_path = os.path.join(self.output_dir, "data.json")
        print(f"Will save data to: {json_path}")

        # Save the data with better error handling
        try:
            print(f"Writing {len(self.data['timestamp'])} data points to {json_path}")
            # Check if directory exists before writing
            if not os.path.exists(os.path.dirname(json_path)):
                print(f"Warning: Directory doesn't exist: {os.path.dirname(json_path)}")
                os.makedirs(os.path.dirname(json_path), exist_ok=True)
                print(f"Created directory: {os.path.dirname(json_path)}")
                
            with open(json_path, 'w') as f:
                json.dump(self.data, f, indent=4)
            
            # Verify file was created
            if os.path.exists(json_path):
                file_size = os.path.getsize(json_path)
                print(f"Data successfully written to {json_path} (size: {file_size} bytes)")
            else:
                print(f"Warning: File not found after writing: {json_path}")
        except Exception as e:
            print(f"Error writing data to {json_path}: {e}")
            # Try writing to current directory as fallback
            fallback_path = "monitor_data.json"
            try:
                print(f"Trying fallback path: {fallback_path}")
                with open(fallback_path, 'w') as f:
                    json.dump(self.data, f, indent=4)
                print(f"Data saved to fallback location: {fallback_path}")
            except Exception as e2:
                print(f"Failed to write data to fallback location: {e2}")
        print(f"Resource monitoring stopped. Collected {len(self.data['timestamp'])} samples")

    def _calculate_and_display_averages(self):
        """Calculate and display average resource usage"""
        if not self.data['timestamp']:
            print("No data collected, cannot calculate averages.")
            return
        
        # Calculate averages
        avg_cpu = sum(self.data['cpu_percent']) / len(self.data['cpu_percent'])
        avg_memory = sum(self.data['memory_percent']) / len(self.data['memory_percent'])
        
        # Calculate total disk I/O
        total_read_bytes = sum(self.data['disk_io_read_bytes'])
        total_write_bytes = sum(self.data['disk_io_write_bytes'])
        total_read_ops = sum(self.data['disk_io_read_ops'])
        total_write_ops = sum(self.data['disk_io_write_ops'])
        
        # Calculate averages per sample
        avg_read_bytes = total_read_bytes / len(self.data['disk_io_read_bytes'])
        avg_write_bytes = total_write_bytes / len(self.data['disk_io_write_bytes'])
        avg_read_ops = total_read_ops / len(self.data['disk_io_read_ops'])
        avg_write_ops = total_write_ops / len(self.data['disk_io_write_ops'])
        
        # Calculate monitoring duration
        if len(self.data['timestamp']) > 1:
            duration = self.data['timestamp'][-1] - self.data['timestamp'][0]
        else:
            duration = 0
        
        # Display results
        print("\n" + "="*60)
        print("RESOURCE USAGE SUMMARY")
        print("="*60)
        print(f"Monitoring Duration: {duration:.2f} seconds")
        print(f"Samples Collected: {len(self.data['timestamp'])}")
        print(f"Sampling Interval: {self.interval} seconds")
        print()
        print("AVERAGES:")
        print(f"  CPU Usage:        {avg_cpu:.2f}%")
        print(f"  Memory Usage:     {avg_memory:.2f}%")
        print(f"  Disk Read Ops:    {avg_read_ops:.2f} ops/sample")
        print(f"  Disk Write Ops:   {avg_write_ops:.2f} ops/sample")
        print(f"  Disk Read Bytes:  {avg_read_bytes:.2f} B/sample")
        print(f"  Disk Write Bytes: {avg_write_bytes:.2f} B/sample")
        print()
        print("TOTALS:")
        print(f"  Total Read Ops:   {total_read_ops:,} operations")
        print(f"  Total Write Ops:  {total_write_ops:,} operations")
        print(f"  Total Read Bytes: {total_read_bytes:,} bytes ({total_read_bytes/1024/1024:.2f} MB)")
        print(f"  Total Write Bytes: {total_write_bytes:,} bytes ({total_write_bytes/1024/1024:.2f} MB)")
        print()
        
        # Find peak usage
        max_cpu = max(self.data['cpu_percent']) if self.data['cpu_percent'] else 0
        max_memory = max(self.data['memory_percent']) if self.data['memory_percent'] else 0
        max_read_ops = max(self.data['disk_io_read_ops']) if self.data['disk_io_read_ops'] else 0
        max_write_ops = max(self.data['disk_io_write_ops']) if self.data['disk_io_write_ops'] else 0
        
        print("PEAK VALUES:")
        print(f"  Peak CPU Usage:    {max_cpu:.2f}%")
        print(f"  Peak Memory Usage: {max_memory:.2f}%")
        print(f"  Peak Read Ops:     {max_read_ops} ops/sample")
        print(f"  Peak Write Ops:    {max_write_ops} ops/sample")
        print("="*60)
        
        # Save summary to file
        summary_data = {
            "monitoring_duration_seconds": duration,
            "samples_collected": len(self.data['timestamp']),
            "sampling_interval": self.interval,
            "averages": {
                "cpu_percent": avg_cpu,
                "memory_percent": avg_memory,
                "disk_read_ops_per_sample": avg_read_ops,
                "disk_write_ops_per_sample": avg_write_ops,
                "disk_read_bytes_per_sample": avg_read_bytes,
                "disk_write_bytes_per_sample": avg_write_bytes
            },
            "totals": {
                "disk_read_ops": total_read_ops,
                "disk_write_ops": total_write_ops,
                "disk_read_bytes": total_read_bytes,
                "disk_write_bytes": total_write_bytes
            },
            "peaks": {
                "cpu_percent": max_cpu,
                "memory_percent": max_memory,
                "disk_read_ops": max_read_ops,
                "disk_write_ops": max_write_ops
            }
        }
        
        try:
            summary_path = os.path.join(self.output_dir, "summary.json")
            with open(summary_path, 'w') as f:
                json.dump(summary_data, f, indent=4)
            print(f"Summary statistics saved to: {summary_path}")
        except Exception as e:
            print(f"Warning: Could not save summary file: {e}")
     
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

            # Add this at the end of your monitoring loop, right before the sleep
            # Periodic save every 100 samples
            if len(self.data['timestamp']) % 100 == 0:
                self._periodic_save()
        
    def _periodic_save(self):
        """Save data periodically to prevent data loss in case of crash"""
        try:
            # Skip if no data
            if not self.data['timestamp']:
                return
                
            # Ensure directory exists
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Save to temporary file first
            temp_path = os.path.join(self.output_dir, "data_temp.json")
            with open(temp_path, 'w') as f:
                json.dump(self.data, f)
                
            # Then rename to final file to avoid partial writes
            final_path = os.path.join(self.output_dir, "data_periodic.json")
            os.replace(temp_path, final_path)
        except Exception as e:
            print(f"\rWarning: Periodic save failed: {e}", end="")
    # end of class ResourceMonitor    

def test_saving():
    """Test that the monitor can save data correctly"""
    test_dir = "test_monitor_save"
    
    # Clean up any previous test data
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)
    
    # Create monitor
    monitor = ResourceMonitor(output_dir=test_dir, interval=0.1)
    
    # Start and collect some data
    monitor.start()
    time.sleep(1)  # Collect data for 1 second
    
    # Stop and check if file was created
    monitor.stop()
    
    json_path = os.path.join(test_dir, "data.json")
    if os.path.exists(json_path):
        print(f"✅ TEST PASSED: Data file was created at {json_path}")
        
        # Check if data was actually saved
        with open(json_path, 'r') as f:
            data = json.load(f)
            if data and len(data['timestamp']) > 0:
                print(f"✅ TEST PASSED: File contains {len(data['timestamp'])} data points")
            else:
                print("❌ TEST FAILED: File exists but contains no data")
    else:
        print(f"❌ TEST FAILED: No data file was created at {json_path}")
    
    # Clean up
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)


def main():
    parser = argparse.ArgumentParser(description='Profile NES binary resource usage')
    parser.add_argument('nes_binary', type=str, help='Path to NES binary executable')
    parser.add_argument('--output', type=str, default=None, help='Output directory for monitoring data')
    parser.add_argument('--interval', type=float, default=0.5, help='Monitoring interval in seconds')
    args = parser.parse_args()

    # Storing the original directory
    original_dir = os.getcwd()
    print(f"Original working directory: {original_dir}")
    
    # Create absolute path for output directory to ensure it's saved in the original location
    if args.output:
        output_dir = os.path.abspath(args.output)
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = os.path.join(original_dir, f"resource_monitor_{timestamp}")
    print(f"Output directory will be: {output_dir}")

     # Create resource monitor
    monitor = ResourceMonitor(output_dir=output_dir, interval=args.interval)

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
        # First change back to the original directory
        print(f"Changing back to original directory: {original_dir}")
        os.chdir(original_dir)

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

# Run the test if called with --test
if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_saving()
    else:
        main()