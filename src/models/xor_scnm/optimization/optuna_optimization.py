#!/usr/bin/env python3
"""
Optuna-based parameter optimization for NETMORPH XOR Circuit.

This script provides multiple optimization methods (Bayesian, TPE, Multi-Objective)
for tuning NETMORPH parameters to maximize convergent neurons in XOR circuits.

Author: Varun Sinha
Date: February 2026

Usage:
    # Bayesian Optimization (Gaussian Process)
    ./optuna_optimization.py --method bayesian --trials 40
    
    # Tree-structured Parzen Estimator
    ./optuna_optimization.py --method tpe --trials 40
    
    # Multi-Objective (neurons, time, timeouts)
    ./optuna_optimization.py --method multi --trials 30
    
    # Resume a previous study
    ./optuna_optimization.py --method bayesian --trials 10 --study-name netmorph_bayesian_20260209_123456
    
    # Visualize results
    optuna-dashboard sqlite:///optuna_results/netmorph_optuna.db

Requirements:
    pip install optuna optuna-dashboard --break-system-packages

Parameter Ranges:
    - B_inf (branching): 5.0 to 20.0
    - growth_nu0 (elongation): 0.0003 to 0.0008
    - turn_separation (turning): 2.0 to 10.0

Success Metric:
    - Target: 10/10 convergent neurons
    - Good: 7-8/10 neurons
    - Marginal: 5-6/10 neurons
    - Failed: <5/10 neurons
"""

import optuna
from optuna.samplers import GPSampler, TPESampler
import argparse
import subprocess
import time
import re
import json
import shutil
from pathlib import Path
from datetime import datetime

# ============================================================================
# NETMORPH CONFIGURATION
# ============================================================================

XOR_DIR = Path.home() / "BrainGenix/BrainEmulationChallenge/src/models/xor_scnm"
CONFIG_FILE = "nesvbp-xor-res-sep-targets"
RESERVOIR_SCRIPT = "./xor_scnm_groundtruth_reservoir.py"
CONNECTOME_SCRIPT = "./xor_scnm_groundtruth_connectome.py"

# Parameter ranges
PARAM_RANGES = {
    'B_inf': (5.0, 20.0),
    'growth_nu0': (0.0003, 0.0008),
    'turn_separation': (2.0, 10.0)
}

# ============================================================================
# CONFIG BACKUP AND MODIFICATION
# ============================================================================

def backup_config():
    """
    Create a timestamped backup of the original config file.
    
    Returns:
        Path: Path to the backup file
    """
    config_path = XOR_DIR / CONFIG_FILE
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = XOR_DIR / f"{CONFIG_FILE}.backup_{timestamp}"
    shutil.copy2(config_path, backup_path)
    
    print(f"✓ Backed up config to: {backup_path.name}")
    return backup_path

def modify_config(B_inf, growth_nu0, turn_separation):
    """
    Modify NETMORPH config file with new parameters.
    
    Args:
        B_inf: Branching time integral parameter
        growth_nu0: Mean elongation rate parameter
        turn_separation: Turning/direction separation parameter
    
    Returns:
        dict: Dictionary of modified parameters
    """
    config_path = XOR_DIR / CONFIG_FILE
    
    # Read config
    with open(config_path, 'r') as f:
        lines = f.readlines()
    
    # Parameters to modify
    params = {
        'all_axons.B_inf': B_inf,
        'all_axons.growth_nu0': growth_nu0,
        'turn_separation': turn_separation
    }
    
    # Modify lines
    modified = {}
    for param_name, value in params.items():
        for i, line in enumerate(lines):
            if line.strip().startswith(param_name + "="):
                lines[i] = f"{param_name}={value};\n"
                modified[param_name] = value
                break
    
    # Write modified config
    with open(config_path, 'w') as f:
        f.writelines(lines)
    
    return modified

# ============================================================================
# NETMORPH EXECUTION
# ============================================================================

def parse_convergent_neurons(output):
    """
    Parse NETMORPH connectome output to extract convergent neuron count.
    
    Args:
        output: String output from connectome script
    
    Returns:
        int or None: Number of convergent neurons, or None if parsing failed
    """
    # Pattern: "List of neurons in PyrMid with inputs from both PyrIn and Int: [1, 2, 3, ...]"
    pattern = r"List of neurons in PyrMid with inputs from both PyrIn and Int: \[([\d, ]+)\]"
    match = re.search(pattern, output)
    
    if match:
        neurons = match.group(1).split(',')
        return len(neurons)
    
    # Check for empty list (0 convergent neurons)
    empty_pattern = r"List of neurons in PyrMid with inputs from both PyrIn and Int: \[\]"
    if re.search(empty_pattern, output):
        return 0
    
    return None

def run_netmorph_simulation(B_inf, growth_nu0, turn_separation):
    """
    Run complete NETMORPH simulation pipeline.
    
    This executes:
    1. Config file modification
    2. Reservoir generation (~11 minutes)
    3. Connectome analysis
    4. Output parsing
    
    Args:
        B_inf: Branching parameter
        growth_nu0: Elongation rate parameter
        turn_separation: Turning parameter
    
    Returns:
        dict: {
            'convergent_neurons': int,
            'elapsed_time': float (seconds),
            'timed_out': bool,
            'success': bool
        }
    """
    start_time = time.time()
    
    try:
        # Step 1: Modify config file
        modify_config(B_inf, growth_nu0, turn_separation)
        
        # Step 2: Run reservoir generation (~11 minutes)
        print(f"    Reservoir...", end='', flush=True)
        reservoir_result = subprocess.run(
            [RESERVOIR_SCRIPT, "-modelfile", CONFIG_FILE, "-Port", "8000"],
            cwd=XOR_DIR,
            capture_output=True,
            text=True,
            timeout=900  # 15 minute timeout
        )
        
        if reservoir_result.returncode != 0:
            elapsed = time.time() - start_time
            print(f" FAILED ({elapsed:.1f}s)")
            return {
                'convergent_neurons': 0,
                'elapsed_time': elapsed,
                'timed_out': False,
                'success': False
            }
        
        print(f" ✓", flush=True)
        
        # Step 3: Run connectome analysis
        print(f"    Connectome...", end='', flush=True)
        connectome_result = subprocess.run(
            [CONNECTOME_SCRIPT],
            cwd=XOR_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if connectome_result.returncode != 0:
            elapsed = time.time() - start_time
            print(f" FAILED ({elapsed:.1f}s)")
            return {
                'convergent_neurons': 0,
                'elapsed_time': elapsed,
                'timed_out': False,
                'success': False
            }
        
        # Step 4: Parse convergent neurons
        convergent = parse_convergent_neurons(connectome_result.stdout)
        elapsed = time.time() - start_time
        
        if convergent is None:
            print(f" PARSE FAILED ({elapsed:.1f}s)")
            return {
                'convergent_neurons': 0,
                'elapsed_time': elapsed,
                'timed_out': False,
                'success': False
            }
        
        print(f" ✓ ({elapsed:.1f}s)")
        
        return {
            'convergent_neurons': convergent,
            'elapsed_time': elapsed,
            'timed_out': False,
            'success': True
        }
        
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f" TIMEOUT ({elapsed:.1f}s)")
        return {
            'convergent_neurons': 0,
            'elapsed_time': elapsed,
            'timed_out': True,
            'success': False
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f" ERROR: {e} ({elapsed:.1f}s)")
        return {
            'convergent_neurons': 0,
            'elapsed_time': elapsed,
            'timed_out': False,
            'success': False
        }

# ============================================================================
# OPTUNA OBJECTIVE FUNCTIONS
# ============================================================================

def objective_single(trial):
    """
    Single-objective optimization: maximize convergent neurons.
    
    Args:
        trial: Optuna trial object
    
    Returns:
        int: Number of convergent neurons (fitness value)
    """
    # Suggest parameters
    B_inf = trial.suggest_float('B_inf', *PARAM_RANGES['B_inf'])
    growth_nu0 = trial.suggest_float('growth_nu0', *PARAM_RANGES['growth_nu0'])
    turn_separation = trial.suggest_float('turn_separation', *PARAM_RANGES['turn_separation'])
    
    # Run simulation
    result = run_netmorph_simulation(B_inf, growth_nu0, turn_separation)
    
    # Store metadata
    trial.set_user_attr('elapsed_time', result['elapsed_time'])
    trial.set_user_attr('timed_out', result['timed_out'])
    trial.set_user_attr('success', result['success'])
    
    # Print trial summary
    print(f"  Trial {trial.number}:")
    print(f"    B_inf={B_inf:.4f}, nu0={growth_nu0:.6f}, turn={turn_separation:.4f}")
    print(f"    → {result['convergent_neurons']}/10 neurons ({result['elapsed_time']:.1f}s)")
    
    # Return fitness (0 if failed)
    return result['convergent_neurons'] if result['success'] else 0

def objective_multi(trial):
    """
    Multi-objective optimization: maximize neurons, minimize time, minimize timeouts.
    
    This provides a Pareto front of trade-offs between:
    - Quality (number of convergent neurons)
    - Speed (elapsed time)
    - Reliability (timeout penalty)
    
    Args:
        trial: Optuna trial object
    
    Returns:
        tuple: (neurons, time, timeout_penalty)
    """
    # Suggest parameters
    B_inf = trial.suggest_float('B_inf', *PARAM_RANGES['B_inf'])
    growth_nu0 = trial.suggest_float('growth_nu0', *PARAM_RANGES['growth_nu0'])
    turn_separation = trial.suggest_float('turn_separation', *PARAM_RANGES['turn_separation'])
    
    # Run simulation
    result = run_netmorph_simulation(B_inf, growth_nu0, turn_separation)
    
    # Extract objectives
    neurons = result['convergent_neurons'] if result['success'] else 0
    time_taken = result['elapsed_time']
    timeout_penalty = 1 if result['timed_out'] else 0
    
    # Print trial summary
    print(f"  Trial {trial.number}:")
    print(f"    B_inf={B_inf:.4f}, nu0={growth_nu0:.6f}, turn={turn_separation:.4f}")
    print(f"    → {neurons}/10 neurons, {time_taken:.1f}s, timeout={timeout_penalty}")
    
    return neurons, time_taken, timeout_penalty

# ============================================================================
# RESULTS REPORTING
# ============================================================================

def print_single_objective_results(study):
    """Print results for single-objective optimization."""
    print(f"\n🏆 Best Result:")
    print(f"  Convergent neurons: {study.best_value}/10")
    print(f"\n  Parameters:")
    print(f"    B_inf          = {study.best_params['B_inf']:.6f}")
    print(f"    growth_nu0     = {study.best_params['growth_nu0']:.6f}")
    print(f"    turn_separation = {study.best_params['turn_separation']:.6f}")
    
    if study.best_trial.user_attrs:
        print(f"\n  Performance:")
        print(f"    Elapsed time: {study.best_trial.user_attrs['elapsed_time']:.1f}s")
        print(f"    Timed out: {study.best_trial.user_attrs['timed_out']}")
        print(f"    Success: {study.best_trial.user_attrs['success']}")

def print_multi_objective_results(study):
    """Print results for multi-objective optimization."""
    print(f"\n📊 Pareto Front: {len(study.best_trials)} optimal trade-off solutions\n")
    
    for i, trial in enumerate(study.best_trials, 1):
        p = trial.params
        v = trial.values
        
        print(f"Solution {i}:")
        print(f"  B_inf={p['B_inf']:.4f}, nu0={p['growth_nu0']:.6f}, turn={p['turn_separation']:.4f}")
        print(f"  → {v[0]}/10 neurons, {v[1]:.1f}s, {v[2]} timeouts")
        print()

def save_results_json(study, args, results_dir):
    """Save study results to JSON file."""
    results_file = results_dir / f"{args.study_name}_results.json"
    
    if args.method == 'multi':
        results = {
            'method': args.method,
            'study_name': args.study_name,
            'n_trials': args.trials,
            'timestamp': datetime.now().isoformat(),
            'pareto_front': [
                {
                    'params': trial.params,
                    'neurons': trial.values[0],
                    'time': trial.values[1],
                    'timeouts': trial.values[2]
                }
                for trial in study.best_trials
            ]
        }
    else:
        results = {
            'method': args.method,
            'study_name': args.study_name,
            'n_trials': args.trials,
            'timestamp': datetime.now().isoformat(),
            'best_value': study.best_value,
            'best_params': study.best_params,
            'best_trial_attrs': study.best_trial.user_attrs if study.best_trial.user_attrs else {}
        }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results_file

# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Optuna optimization for NETMORPH parameters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

Bayesian Optimization (40 trials, ~7-8 hours):
  ./optuna_optimization.py --method bayesian --trials 40

TPE Optimization (40 trials, ~7-8 hours):
  ./optuna_optimization.py --method tpe --trials 40

Multi-Objective (30 trials, ~5-6 hours):
  ./optuna_optimization.py --method multi --trials 30

Resume a study:
  ./optuna_optimization.py --method bayesian --trials 10 --study-name netmorph_bayesian_20260209_123456

Visualize results:
  optuna-dashboard sqlite:///optuna_results/netmorph_optuna.db
        """
    )
    
    parser.add_argument('--method', 
                       choices=['bayesian', 'tpe', 'multi'], 
                       default='bayesian',
                       help='Optimization method (default: bayesian)')
    parser.add_argument('--trials', 
                       type=int, 
                       default=40,
                       help='Number of optimization trials (default: 40)')
    parser.add_argument('--study-name', 
                       type=str, 
                       default=None,
                       help='Study name for resuming or custom naming')
    
    args = parser.parse_args()
    
    # Generate study name if not provided
    if args.study_name is None:
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        args.study_name = f'netmorph_{args.method}_{timestamp}'
    
    # Create results directory
    results_dir = Path('optuna_results')
    results_dir.mkdir(exist_ok=True)
    storage = f'sqlite:///{results_dir}/netmorph_optuna.db'
    
    # Print header
    print("\n" + "="*70)
    print(f"🚀 OPTUNA OPTIMIZATION FOR NETMORPH - {args.method.upper()}")
    print("="*70)
    print(f"Study name:  {args.study_name}")
    print(f"Trials:      {args.trials}")
    print(f"Storage:     {storage}")
    print(f"Results dir: {results_dir}")
    
    # Backup config
    try:
        backup_path = backup_config()
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you're running from the optimization directory.")
        return 1
    
    print("="*70 + "\n")
    
    # Create sampler based on method
    if args.method == 'bayesian':
        sampler = GPSampler(n_startup_trials=8, seed=42)
        print("Method: Gaussian Process (Bayesian Optimization)")
        print("  - Builds surrogate model of parameter → performance")
        print("  - Balances exploration vs exploitation")
        print("  - Optimal for 3-10 dimensional problems")
    elif args.method == 'tpe':
        sampler = TPESampler(n_startup_trials=8, seed=42)
        print("Method: Tree-structured Parzen Estimator (TPE)")
        print("  - Models p(parameters|performance)")
        print("  - Efficient for high-dimensional spaces")
        print("  - Handles mixed parameter types well")
    else:  # multi
        sampler = GPSampler(seed=42)
        print("Method: Multi-Objective Gaussian Process")
        print("  - Optimizes neurons, time, and reliability simultaneously")
        print("  - Returns Pareto front of optimal trade-offs")
        print("  - Ideal for understanding speed/quality balance")
    
    print(f"\nParameter ranges:")
    for param, (low, high) in PARAM_RANGES.items():
        print(f"  {param:20s}: [{low}, {high}]")
    
    print(f"\nEstimated time: ~{args.trials * 11 / 60:.1f} hours")
    print("="*70 + "\n")
    
    # Create study
    if args.method == 'multi':
        study = optuna.create_study(
            study_name=args.study_name,
            storage=storage,
            directions=['maximize', 'minimize', 'minimize'],  # neurons, time, timeouts
            sampler=sampler,
            load_if_exists=True
        )
        objective = objective_multi
    else:
        study = optuna.create_study(
            study_name=args.study_name,
            storage=storage,
            direction='maximize',  # maximize convergent neurons
            sampler=sampler,
            load_if_exists=True
        )
        objective = objective_single
    
    # Run optimization
    print("Starting optimization...\n")
    study.optimize(objective, n_trials=args.trials)
    
    # Print results
    print("\n" + "="*70)
    print("✅ OPTIMIZATION COMPLETE")
    print("="*70)
    
    if args.method == 'multi':
        print_multi_objective_results(study)
    else:
        print_single_objective_results(study)
    
    # Save results
    results_file = save_results_json(study, args, results_dir)
    
    print("\n" + "="*70)
    print("📁 Output Files:")
    print("="*70)
    print(f"  Database:  {storage}")
    print(f"  Results:   {results_file}")
    print(f"  Backup:    {backup_path.name}")
    
    print("\n" + "="*70)
    print("📈 Next Steps:")
    print("="*70)
    print(f"  Visualize: optuna-dashboard {storage}")
    print(f"  Compare:   Compare with scikit-optimize results")
    print(f"  Expand:    Consider adding parameters (E, lin-mn, tau)")
    print("="*70 + "\n")
    
    return 0

if __name__ == '__main__':
    exit(main())