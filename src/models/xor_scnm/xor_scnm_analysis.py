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
import shutil
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

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

    @classmethod    
    def aggregate_runs_to_csv(cls, base_output_dir, output_filename="aggregated_results.csv"):
        """
        Aggregates all run data from subdirectories into a single CSV file.
        
        Args:
            base_output_dir: Directory containing all the run subdirectories
            output_filename: Name for the output CSV file
        """
        import csv
        import glob
        
        # Find all data.json files in subdirectories
        data_files = glob.glob(os.path.join(base_output_dir, "*/data.json"))
        
        if not data_files:
            print(f"No data files found in {base_output_dir}")
            return
        
        # Prepare CSV output
        csv_path = os.path.join(base_output_dir, output_filename)
        print(f"\nAggregating data from {len(data_files)} runs to {csv_path}")
        
        # Field names for CSV (we'll use the same as in data.json plus a run_id column)
        fieldnames = ['run_id', 'timestamp', 'cpu_percent', 'memory_percent', 
                    'disk_io_read_bytes', 'disk_io_write_bytes',
                    'disk_io_read_ops', 'disk_io_write_ops']
        
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for data_file in sorted(data_files):
                # Extract run ID from directory name
                run_dir = os.path.dirname(data_file)
                run_id = os.path.basename(run_dir)
                
                try:
                    with open(data_file, 'r') as f:
                        data = json.load(f)
                    
                    # Write each data point with run_id
                    for i in range(len(data['timestamp'])):
                        row = {
                            'run_id': run_id,
                            'timestamp': data['timestamp'][i],
                            'cpu_percent': data['cpu_percent'][i],
                            'memory_percent': data['memory_percent'][i],
                            'disk_io_read_bytes': data['disk_io_read_bytes'][i],
                            'disk_io_write_bytes': data['disk_io_write_bytes'][i],
                            'disk_io_read_ops': data['disk_io_read_ops'][i],
                            'disk_io_write_ops': data['disk_io_write_ops'][i]
                        }
                        writer.writerow(row)
                    
                    print(f"Processed {len(data['timestamp'])} samples from {run_id}")
                except Exception as e:
                    print(f"Error processing {data_file}: {e}")
        
        print(f"Aggregation complete. CSV saved to {csv_path}")

    @staticmethod
    def create_simple_graphs(csv_file_path, output_dir=None):
        """
        Create simple interactive graphs from CSV data.
        """
        try:
            import pandas as pd
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            import os
        except ImportError:
            print("Error: Install required packages with: pip install pandas plotly")
            return

        # Read CSV
        try:
            df = pd.read_csv(csv_file_path)
            print(f"Loaded data: {len(df)} rows")
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return

        # Set output directory
        if output_dir is None:
            output_dir = os.path.dirname(csv_file_path)
        
        # Convert timestamp to relative time
        df['relative_time'] = df.groupby('run_id')['timestamp'].transform(lambda x: x - x.min())
        
        # Get unique runs
        runs = df['run_id'].unique()
        print(f"Found runs: {runs}")
        
        # Create simple 2x2 dashboard
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('CPU Usage (%)', 'Memory Usage (%)', 
                        'Disk Read Bytes', 'Disk Write Bytes')
        )
        
        # Color palette
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        
        for i, run in enumerate(runs):
            run_data = df[df['run_id'] == run]
            color = colors[i % len(colors)]
            
            # CPU Usage
            fig.add_trace(
                go.Scatter(
                    x=run_data['relative_time'],
                    y=run_data['cpu_percent'],
                    mode='lines',
                    name=f'{run}',
                    line=dict(color=color),
                    legendgroup=run
                ),
                row=1, col=1
            )
            
            # Memory Usage
            fig.add_trace(
                go.Scatter(
                    x=run_data['relative_time'],
                    y=run_data['memory_percent'],
                    mode='lines',
                    name=f'{run}',
                    line=dict(color=color),
                    legendgroup=run,
                    showlegend=False
                ),
                row=1, col=2
            )
            
            # Disk Read
            fig.add_trace(
                go.Scatter(
                    x=run_data['relative_time'],
                    y=run_data['disk_io_read_bytes'],
                    mode='lines',
                    name=f'{run}',
                    line=dict(color=color),
                    legendgroup=run,
                    showlegend=False
                ),
                row=2, col=1
            )
            
            # Disk Write
            fig.add_trace(
                go.Scatter(
                    x=run_data['relative_time'],
                    y=run_data['disk_io_write_bytes'],
                    mode='lines',
                    name=f'{run}',
                    line=dict(color=color),
                    legendgroup=run,
                    showlegend=False
                ),
                row=2, col=2
            )
        
        # Update axis labels
        fig.update_xaxes(title_text="Time (seconds)", row=1, col=1)
        fig.update_xaxes(title_text="Time (seconds)", row=1, col=2)
        fig.update_xaxes(title_text="Time (seconds)", row=2, col=1)
        fig.update_xaxes(title_text="Time (seconds)", row=2, col=2)
        
        fig.update_yaxes(title_text="CPU Usage (%)", row=1, col=1)
        fig.update_yaxes(title_text="Memory Usage (%)", row=1, col=2)
        fig.update_yaxes(title_text="Read Bytes/sec", row=2, col=1)
        fig.update_yaxes(title_text="Write Bytes/sec", row=2, col=2)
        
        # Update layout
        fig.update_layout(
            title="Performance Summary Dashboard",
            height=600,
            showlegend=True,
            hovermode='x unified'
        )
        
        # Save the graph
        output_path = os.path.join(output_dir, "performance_summary.html")
        fig.write_html(output_path)
        print(f"Graph saved to: {output_path}")
        
        # Create summary stats table
        summary = df.groupby('run_id').agg({
            'cpu_percent': ['mean', 'max'],
            'memory_percent': ['mean', 'max'],
            'disk_io_read_bytes': 'sum',
            'disk_io_write_bytes': 'sum'
        }).round(2)
        
        # Save summary as CSV
        summary_path = os.path.join(output_dir, "run_summary.csv")
        summary.to_csv(summary_path)
        print(f"Summary saved to: {summary_path}")
        
        return output_path
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
        print(f"TEST PASSED: Data file was created at {json_path}")
        
        # Check if data was actually saved
        with open(json_path, 'r') as f:
            data = json.load(f)
            if data and len(data['timestamp']) > 0:
                print(f"TEST PASSED: File contains {len(data['timestamp'])} data points")
            else:
                print("TEST FAILED: File exists but contains no data")
    else:
        print(f"TEST FAILED: No data file was created at {json_path}")
    
    # Clean up
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)


def main():
    parser = argparse.ArgumentParser(description='Profile NES binary resource usage')
    parser.add_argument('nes_binary', type=str, help='Path to NES binary executable')
    parser.add_argument('run_script', type=str, help='Path to run script')
    parser.add_argument('--output', type=str, default=None, help='Output directory for monitoring data')
    parser.add_argument('--interval', type=float, default=0.5, help='Monitoring interval in seconds')
    parser.add_argument('--runs', type=int, default=5, help='Number of runs to execute')
    parser.add_argument('--argumentfile', type=str, default=None, help='Path to txt file with each set of arguments you wish to run, comma separated, followed by newline (\\n)')
    args = parser.parse_args()

    original_dir = os.getcwd()
    print(f"Original working directory: {original_dir}")

    # Load argument file
    ArgList = [["-x a","-s","40"]] # Default arglist values
    ArgumentFilePath = args.argumentfile
    if (ArgumentFilePath):
        with open(ArgumentFilePath, "r") as File:
            ArgList = File.read().split("\n")
        for i in range(len(ArgList)):
            ArgList[i] = ArgList[i].split(",")
        
        print(f"Loaded Argument List, Parsed {len(ArgList)} ")
        print(f"double checking arList: {ArgList}")
    else:
        print(f"No argument file path provided, defaulting to: {ArgList}")

    for ArgRunIndex in range(len(ArgList)):
        if args.output:
            base_output_dir = os.path.abspath(f"{args.output}{ArgList[ArgRunIndex]}")
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            script_name = '_'.join(ArgList[ArgRunIndex])
            base_output_dir = os.path.join(original_dir, f"{script_name}")

        script_full_path = os.path.abspath(args.run_script)
        print(f"Run script will be: {script_full_path}")

        CurrentArguments = ArgList[ArgRunIndex]

        print(f"Running Run.sh with Arguments: {CurrentArguments}")

        for run_number in range(1, args.runs + 1):
            print(f"\n{'='*60}\nSTARTING RUN {run_number} of {args.runs}\n{'='*60}")
            print("Performing pre-run cleanup...")
            
            # Clean up any existing directories first
            renders_path = os.path.join(os.path.dirname(args.nes_binary), "Renders")
            datasets_path = os.path.join(os.path.dirname(args.nes_binary), "NueroglancerDatasets")
            
            for cleanup_path in [renders_path, datasets_path]:
                if os.path.exists(cleanup_path):
                    try:
                        shutil.rmtree(cleanup_path)
                        print(f"Pre-cleanup: Deleted directory: {cleanup_path}")
                    except Exception as e:
                        print(f"Warning: Could not delete {cleanup_path}: {e}")

            # Kill any existing processes that might interfere
            binary_name = os.path.basename(args.nes_binary)
            script_name = os.path.basename(script_full_path)

            try:
                # For NES binary - kill by exact process name
                process.kill()
                RunScript.kill()
                
                print("Process cleanup completed")
                time.sleep(2)  # Wait for processes to fully terminate
                
            except Exception as e:
                print(f"Warning during process cleanup: {e}") 
            
            # Wait for system to stabilize
            print("Waiting for system to stabilize...")
            time.sleep(3)
            
            # Unique output directory for each run
            output_dir = os.path.join(base_output_dir, f"run_{run_number:02d}")
            print(f"Output directory will be: {output_dir}")

            monitor = ResourceMonitor(output_dir=output_dir, interval=args.interval)
            process = None
            RunScript = None

            try:
                # FRESH START FOR EACH RUN
                print("Starting fresh processes...")
                
                # Start NES binary
                binary_dir = os.path.dirname(args.nes_binary)
                os.chdir(binary_dir)
                
                process = subprocess.Popen([f"./{binary_name}"])
                print(f"Started NES process with PID: {process.pid}")

                # Wait longer for NES to fully initialize
                print("Waiting for NES to fully initialize...")
                time.sleep(3)  

                # Start Run script
                script_dir = os.path.dirname(script_full_path)
                os.chdir(script_dir)
                print(f"Starting script: {script_name}")
                
                RunList = [f"./{script_name}"] + CurrentArguments
                RunScript = subprocess.Popen(RunList)
                print(f"Started script process with PID: {RunScript.pid}")

                # Start monitoring ONLY after both processes are running
                print("Starting resource monitoring...")
                monitor.start()

                # Wait for RunScript to complete
                while RunScript.poll() is None:
                    time.sleep(0.1)
                print(f"Script completed with return code: {RunScript.returncode}")
            except KeyboardInterrupt:
                print("\nKeyboard interrupt received. Stopping...")
                break
            except Exception as e:
                print(f"Error during run {run_number}: {e}")
            finally:
                print(f"Cleaning up run {run_number}...")
                
                # Change back to original directory
                os.chdir(original_dir)

                # Stop monitoring first
                monitor.stop()

                # Terminate processes more aggressively
                if process and process.poll() is None:
                    print("Terminating NES binary...")
                    try:
                        process.send_signal(signal.SIGTERM)  
                        process.wait(timeout=3.0)
                    except subprocess.TimeoutExpired:
                        print("Force killing NES binary...")
                        process.kill()
                        process.wait(timeout=1.0)

                if RunScript and RunScript.poll() is None:
                    print("Terminating Run Script...")
                    try:
                        RunScript.send_signal(signal.SIGTERM)  
                        RunScript.wait(timeout=3.0)
                    except subprocess.TimeoutExpired:
                        print("Force killing Run Script...")
                        RunScript.kill()
                        RunScript.wait(timeout=1.0)

                # Clean up output directories
                for cleanup_path in [renders_path, datasets_path]:
                    if os.path.exists(cleanup_path):
                        try:
                            shutil.rmtree(cleanup_path)
                            print(f"Post-cleanup: Deleted directory: {cleanup_path}")
                        except Exception as e:
                            print(f"Warning: Could not delete {cleanup_path}: {e}")

                print(f"Run {run_number} cleanup completed")

            # Wait longer between runs to ensure complete cleanup
            if run_number < args.runs:
                print(f"Waiting 10 seconds before starting run {run_number + 1}...")
                time.sleep(10)  

        print(f"\n{'='*60}\nALL {args.runs} RUNS COMPLETED\n{'='*60}")
        print(f"Data saved in: {base_output_dir}")

        csv_path = os.path.join(base_output_dir, "aggregated_results.csv")
        ResourceMonitor.aggregate_runs_to_csv(base_output_dir)

        # Create interactive graphs
        if os.path.exists(csv_path):
            print("Creating simple performance graph...")
            try:
                ResourceMonitor.create_simple_graphs(csv_path, base_output_dir)
            except Exception as e:
                print(f"Error creating graphs: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Warning: CSV file not found at {csv_path}")

# Run the test if called with --test
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_saving()
    else:
        main()