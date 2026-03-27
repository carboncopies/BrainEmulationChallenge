#!/usr/bin/env python3
"""
Bayesian Optimization for NETMORPH Parameter Tuning

Author: Varun Sinha
Date: December 23, 2025


Uses Gaussian Process to intelligently search parameter space.
Finds optimal parameters in ~30 tests instead of 200+ with grid search.

Usage:
    ./bayesian_optimization.py --n-calls 30

Reference: https://carboncopiespythondev.atlassian.net/wiki/spaces/PCD/pages/35356687/Fall+2025+internship+Netmorph+development
"""

import numpy as np
import pandas as pd
from skopt import gp_minimize
from skopt.space import Real
from skopt.utils import use_named_args
import argparse
import time
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime

# Paths
XOR_DIR = Path.home() / "BrainGenix/BrainEmulationChallenge/src/models/xor_scnm"
CONFIG_FILE = "nesvbp-xor-res-sep-targets"
RESERVOIR_SCRIPT = "./xor_scnm_groundtruth_reservoir.py"
CONNECTOME_SCRIPT = "./xor_scnm_groundtruth_connectome.py"

# Define parameter search space
param_space = [
    Real(5.0, 20.0, name='all_axons.B_inf'),
    Real(0.0003, 0.0008, name='all_axons.growth_nu0'),
    Real(2.0, 10.0, name='turn_separation')
]

class BayesianOptimizer:
    def __init__(self):
        self.test_count = 0
        self.results_history = []
        self.config_backup = None
        self.log_dir = Path("bayesian_logs")
        self.log_dir.mkdir(exist_ok=True)
        
    def backup_config(self):
        """Backup original config file"""
        config_path = XOR_DIR / CONFIG_FILE
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config_backup = self.log_dir / f"{CONFIG_FILE}.backup_{timestamp}"
        shutil.copy2(config_path, self.config_backup)
        print(f"✓ Backed up config to: {self.config_backup}\n")
        
    def restore_config(self):
        """Restore original config file"""
        if self.config_backup and self.config_backup.exists():
            config_path = XOR_DIR / CONFIG_FILE
            shutil.copy2(self.config_backup, config_path)
            print(f"\n✓ Restored original config")
            
    def modify_config(self, B_inf, growth_nu0, turn_separation):
        """Modify config file with new parameters"""
        config_path = XOR_DIR / CONFIG_FILE
        
        with open(config_path, 'r') as f:
            lines = f.readlines()
        
        params = {
            'all_axons.B_inf': B_inf,
            'all_axons.growth_nu0': growth_nu0,
            'turn_separation': turn_separation
        }
        
        for param_name, value in params.items():
            for i, line in enumerate(lines):
                if line.strip().startswith(param_name + "="):
                    lines[i] = f"{param_name}={value};\n"
                    break
        
        with open(config_path, 'w') as f:
            f.writelines(lines)
            
    def run_reservoir(self, test_id):
        """Run reservoir generation"""
        log_file = self.log_dir / f"test_{test_id}_reservoir.log"
        
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
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"  ✗ Reservoir timed out!")
            return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
            
    def run_connectome(self, test_id):
        """Run connectome analysis and parse results"""
        log_file = self.log_dir / f"test_{test_id}_connectome.log"
        
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
                return None
            
            # Parse convergent neurons
            pattern = r"List of neurons in PyrMid with inputs from both PyrIn and Int: \[([\d, ]+)\]"
            match = re.search(pattern, result.stdout)
            
            if match:
                neurons = match.group(1).split(',')
                return len(neurons)
            
            # Handle empty list
            empty_pattern = r"List of neurons in PyrMid with inputs from both PyrIn and Int: \[\]"
            if re.search(empty_pattern, result.stdout):
                return 0
                
            return None
            
        except subprocess.TimeoutExpired:
            print(f"  ✗ Connectome timed out!")
            return None
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None
            
    def format_time(self, seconds):
        """Format elapsed time as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
        
    def objective_function(self, params):
        """
        Objective function for optimization.
        Runs one actual NETMORPH test and returns negative convergent neurons
        (negative because optimizer minimizes by default, we want to maximize)
        """
        B_inf, growth_nu0, turn_separation = params
        
        self.test_count += 1
        test_id = self.test_count
        
        print(f"\n{'='*70}")
        print(f"Bayesian Optimization - Test {test_id}")
        print(f"{'='*70}")
        print(f"Parameters:")
        print(f"  all_axons.B_inf = {B_inf:.4f}")
        print(f"  all_axons.growth_nu0 = {growth_nu0:.6f}")
        print(f"  turn_separation = {turn_separation:.4f}")
        print(f"{'='*70}")
        
        start_time = time.time()
        
        # Modify config
        self.modify_config(B_inf, growth_nu0, turn_separation)
        print("  ✓ Modified config")
        
        # Run reservoir
        print("  Running reservoir generation... (~11 minutes)")
        if not self.run_reservoir(test_id):
            elapsed = time.time() - start_time
            elapsed_str = self.format_time(elapsed)
            
            result = {
                'test_id': test_id,
                'all_axons.B_inf': B_inf,
                'all_axons.growth_nu0': growth_nu0,
                'turn_separation': turn_separation,
                'convergent_neurons': 0,
                'percentage': '0%',
                'status': '✗ Failed',
                'elapsed_time': elapsed_str
            }
            self.results_history.append(result)
            self.save_results()
            
            print(f"  ✗ Test failed - Elapsed time: {elapsed_str}")
            return 0.0  # Return 0 (worst possible score)
        
        print("  ✓ Reservoir complete")
        
        # Run connectome
        print("  Running connectome analysis...")
        convergent = self.run_connectome(test_id)
        
        elapsed = time.time() - start_time
        elapsed_str = self.format_time(elapsed)
        
        if convergent is None:
            convergent = 0
            status = '✗ Failed'
            percentage = '0%'
        else:
            percentage = f"{int((convergent/10)*100)}%"
            if convergent >= 9:
                status = '✓ Excellent'
            elif convergent >= 7:
                status = '✓ Good'
            elif convergent >= 5:
                status = '⚠️ Marginal'
            else:
                status = '✗ Failed'
        
        print(f"  ✓ Connectome complete: {convergent}/10 convergent neurons")
        print(f"  Result: {status} ({percentage})")
        print(f"  Elapsed time: {elapsed_str}")
        
        # Save result
        result = {
            'test_id': test_id,
            'all_axons.B_inf': B_inf,
            'all_axons.growth_nu0': growth_nu0,
            'turn_separation': turn_separation,
            'convergent_neurons': convergent,
            'percentage': percentage,
            'status': status,
            'elapsed_time': elapsed_str
        }
        self.results_history.append(result)
        self.save_results()
        
        # Return negative because optimizer MINIMIZES
        # We want to MAXIMIZE convergent neurons
        return -float(convergent)
        
    def save_results(self):
        """Save results to CSV"""
        df = pd.DataFrame(self.results_history)
        output_file = "bayesian_optimization_results.csv"
        df.to_csv(output_file, index=False)
        print(f"  ✓ Results saved to: {output_file}")
        
    def print_summary(self):
        """Print optimization summary"""
        df = pd.DataFrame(self.results_history)
        
        print("\n" + "="*70)
        print("BAYESIAN OPTIMIZATION SUMMARY")
        print("="*70)
        
        # Best result
        best_idx = df['convergent_neurons'].astype(float).idxmax()
        best = df.iloc[best_idx]
        
        print(f"\nBest Parameters Found:")
        print(f"  all_axons.B_inf: {best['all_axons.B_inf']:.4f}")
        print(f"  all_axons.growth_nu0: {best['all_axons.growth_nu0']:.6f}")
        print(f"  turn_separation: {best['turn_separation']:.4f}")
        print(f"  Result: {best['convergent_neurons']}/10 neurons ({best['percentage']})")
        print(f"  Time: {best['elapsed_time']}")
        print(f"  Status: {best['status']}")
        
        # Statistics
        print(f"\nOptimization Statistics:")
        print(f"  Total tests run: {len(df)}")
        print(f"  Tests with 10/10: {len(df[df['convergent_neurons'] == 10])}")
        print(f"  Tests with 9+/10: {len(df[df['convergent_neurons'] >= 9])}")
        print(f"  Failed tests: {len(df[df['convergent_neurons'] == 0])}")
        
        # Total time
        total_minutes = sum([int(t.split(':')[0]) for t in df['elapsed_time']]) + \
                       sum([int(t.split(':')[1]) for t in df['elapsed_time']]) / 60
        print(f"  Total time: {total_minutes:.1f} minutes ({total_minutes/60:.1f} hours)")
        
        print("="*70)
        print(f"\nDetailed results saved to: bayesian_optimization_results.csv")
        print(f"Logs saved to: bayesian_logs/")
        print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Bayesian Optimization for NETMORPH parameters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    # Run 30 intelligent tests to find optimal parameters
    ./bayesian_optimization.py --n-calls 30
    
    # Quick test with 10 iterations
    ./bayesian_optimization.py --n-calls 10
    
    # Longer optimization
    ./bayesian_optimization.py --n-calls 50
        """
    )
    
    parser.add_argument('--n-calls', type=int, default=30,
                       help='Number of optimization iterations (default: 30)')
    parser.add_argument('--n-initial', type=int, default=5,
                       help='Number of random initial tests (default: 5)')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("BAYESIAN OPTIMIZATION FOR NETMORPH PARAMETERS")
    print("="*70)
    print(f"Total tests to run: {args.n_calls}")
    print(f"Initial random exploration: {args.n_initial}")
    print(f"Smart optimization: {args.n_calls - args.n_initial}")
    print(f"Estimated total time: ~{args.n_calls * 11} minutes ({args.n_calls * 11 / 60:.1f} hours)")
    print("="*70 + "\n")
    
    # Initialize optimizer
    optimizer = BayesianOptimizer()
    optimizer.backup_config()
    
    try:
        # Run Bayesian optimization
        result = gp_minimize(
            func=optimizer.objective_function,
            dimensions=param_space,
            n_calls=args.n_calls,
            n_initial_points=args.n_initial,
            random_state=42,
            verbose=False 
        )
        
        # Print summary
        optimizer.print_summary()
        
    finally:
        # Always restore config
        optimizer.restore_config()
    
    return 0


if __name__ == "__main__":
    exit(main())
