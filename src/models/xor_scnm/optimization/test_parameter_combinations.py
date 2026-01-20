#!/usr/bin/env python3
import pandas as pd
import subprocess
import re
import shutil
import time
import sys
import argparse
from pathlib import Path
from datetime import datetime

XOR_DIR = Path.home() / "BrainGenix/BrainEmulationChallenge/src/models/xor_scnm"
CONFIG_FILE = "nesvbp-xor-res-sep-targets"
RESERVOIR_SCRIPT = "./xor_scnm_groundtruth_reservoir.py"
CONNECTOME_SCRIPT = "./xor_scnm_groundtruth_connectome.py"

class CSVParameterTester:
    def __init__(self, csv_file, test_ids=None):
        self.csv_file = Path(csv_file)
        self.test_ids = test_ids
        self.config_backup = None
        self.log_dir = Path("csv_test_logs")
        self.log_dir.mkdir(exist_ok=True)
        
    def backup_config(self):
        config_path = XOR_DIR / CONFIG_FILE
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config_backup = self.log_dir / f"{CONFIG_FILE}.backup_{timestamp}"
        shutil.copy2(config_path, self.config_backup)
        print(f"✓ Backed up config to: {self.config_backup}")
    
    def restore_config(self):
        if self.config_backup and self.config_backup.exists():
            config_path = XOR_DIR / CONFIG_FILE
            shutil.copy2(self.config_backup, config_path)
            print(f"✓ Restored original config")
    
    def modify_config(self, params):
        config_path = XOR_DIR / CONFIG_FILE
        
        with open(config_path, 'r') as f:
            lines = f.readlines()
        
        modified = {}
        
        for param_name, value in params.items():
            for i, line in enumerate(lines):
                if line.strip().startswith(param_name + "="):
                    lines[i] = f"{param_name}={value};\n"
                    modified[param_name] = value
                    break
        
        with open(config_path, 'w') as f:
            f.writelines(lines)
        
        return modified
    
    def run_reservoir(self, test_id):
        log_file = self.log_dir / f"test_{test_id}_reservoir.log"
        
        print(f"  Running reservoir generation... (~11 minutes)")
        
        try:
            result = subprocess.run(
                [RESERVOIR_SCRIPT, "-modelfile", CONFIG_FILE, "-Port", "8000"],
                cwd=XOR_DIR,
                capture_output=True,
                text=True,
                timeout=900
            )
            
            with open(log_file, 'w') as f:
                f.write(result.stdout)
                f.write(result.stderr)
            
            if result.returncode != 0:
                print(f"  ✗ Reservoir generation failed!")
                return False
            
            print(f"  ✓ Reservoir complete")
            return True
            
        except subprocess.TimeoutExpired:
            print(f"  ✗ Reservoir timed out!")
            return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def run_connectome(self, test_id):
        log_file = self.log_dir / f"test_{test_id}_connectome.log"
        
        print(f"  Running connectome analysis...")
        
        try:
            result = subprocess.run(
                [CONNECTOME_SCRIPT],
                cwd=XOR_DIR,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            with open(log_file, 'w') as f:
                f.write(result.stdout)
                f.write(result.stderr)
            
            if result.returncode != 0:
                print(f"  ✗ Connectome failed!")
                return None
            
            convergent = self.parse_convergent_neurons(result.stdout)
            
            if convergent is not None:
                print(f"  ✓ Connectome complete: {convergent}/10 convergent neurons")
            
            return convergent
            
        except subprocess.TimeoutExpired:
            print(f"  ✗ Connectome timed out!")
            return None
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None
    
    def parse_convergent_neurons(self, output):
        pattern = r"List of neurons in PyrMid with inputs from both PyrIn and Int: \[([\d, ]+)\]"
        match = re.search(pattern, output)
        
        if match:
            neurons = match.group(1).split(',')
            return len(neurons)
        
        empty_pattern = r"List of neurons in PyrMid with inputs from both PyrIn and Int: \[\]"
        if re.search(empty_pattern, output):
            return 0
            
        return None
    
    def classify_result(self, convergent_count):
        if convergent_count is None:
            return "✗ Failed", "0%"
        
        percentage = (convergent_count / 10) * 100
        
        if percentage <= 40:
            return "✗ Failed", f"{int(percentage)}%"
        elif percentage <= 60:
            return "⚠️ Marginal", f"{int(percentage)}%"
        elif percentage <= 85:
            return "✓ Good", f"{int(percentage)}%"
        else:
            return "✓ Excellent", f"{int(percentage)}%"
    
    # elapsed time function
    def format_elapsed_time(self, seconds):
        """Format elapsed time as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def run_tests(self):
        print("\n" + "="*60)
        print("NETMORPH Multi-Parameter Testing (pandas version)")
        print(f"CSV File: {self.csv_file}")
        print("="*60 + "\n")
        
        df = pd.read_csv(self.csv_file)
        
        if 'elapsed_time' not in df.columns:
            df['elapsed_time'] = ''
        
        if self.test_ids:
            df = df[df['test_id'].isin(self.test_ids)]
            print(f"Running only tests: {self.test_ids}")
            print()
        
        if df.empty:
            print("No tests to run!")
            return
        
        self.backup_config()
        
        try:
            for idx, row in df.iterrows():
                print(f"\n{'='*60}")
                print(f"Test {idx+1}/{len(df)} (ID: {row['test_id']})")
                print(f"Note: {row['notes']}")
                print(f"{'='*60}")
                
                start_time = time.time()
                
                params = {
                    'all_axons.B_inf': row['all_axons.B_inf'],
                    'all_axons.growth_nu0': row['all_axons.growth_nu0'],
                    'turn_separation': row['turn_separation']
                }
                
                print(f"  Parameters:")
                for k, v in params.items():
                    print(f"    {k} = {v}")
                
                modified = self.modify_config(params)
                print(f"  ✓ Modified config")
                
                if not self.run_reservoir(row['test_id']):
                    elapsed = time.time() - start_time
                    df.at[idx, 'convergent_neurons'] = 'N/A'
                    df.at[idx, 'percentage'] = '0%'
                    df.at[idx, 'status'] = '✗ Failed'
                    df.at[idx, 'elapsed_time'] = self.format_elapsed_time(elapsed)
                else:
                    convergent = self.run_connectome(row['test_id'])
                    elapsed = time.time() - start_time
                    status, percentage = self.classify_result(convergent)
                    
                    df.at[idx, 'convergent_neurons'] = convergent if convergent is not None else 'N/A'
                    df.at[idx, 'percentage'] = percentage
                    df.at[idx, 'status'] = status
                    df.at[idx, 'elapsed_time'] = self.format_elapsed_time(elapsed)
                
                self.write_results(df)
                
                print(f"  Result: {df.at[idx, 'status']} ({df.at[idx, 'percentage']})")
                print(f"  Elapsed time: {df.at[idx, 'elapsed_time']}")
                
                if idx < len(df) - 1:
                    print(f"\n  Waiting 5 seconds before next test...")
                    time.sleep(5)
        
        finally:
            self.restore_config()
        
        self.print_summary(df)
    
    def write_results(self, df):
        output_file = self.csv_file.parent / f"{self.csv_file.stem}_results.csv"
        df.to_csv(output_file, index=False)
        print(f"\n  ✓ Results saved to: {output_file}")
    
    def print_summary(self, df):
        print("\n" + "="*60)
        print("RESULTS SUMMARY")
        print("="*60 + "\n")
        
        print(f"{'ID':<4} {'B_inf':<8} {'growth_nu0':<12} {'turn_sep':<10} {'Conv':<8} {'Time':<8} {'Status':<15}")
        print("-"*70)
        
        for idx, row in df.iterrows():
            print(f"{row['test_id']:<4} {row['all_axons.B_inf']:<8} {row['all_axons.growth_nu0']:<12} "
                  f"{row['turn_separation']:<10} {row['convergent_neurons']:<8} {row['elapsed_time']:<8} {row['status']:<15}")
        
        print("\n" + "="*60)
        print(f"✓ Complete! Check csv_test_logs/ for detailed logs")
        print("="*60 + "\n")

def main():
    parser = argparse.ArgumentParser(description='Test NETMORPH parameter combinations')
    parser.add_argument('csv_file', help='CSV file with parameter combinations')
    parser.add_argument('--test-ids', type=int, nargs='+', 
                       help='Specific test IDs to run (e.g., --test-ids 1 3 5)')
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"Error: CSV file '{args.csv_file}' not found")
        return 1
    
    tester = CSVParameterTester(args.csv_file, args.test_ids)
    tester.run_tests()
    
    return 0

if __name__ == "__main__":
    exit(main())
