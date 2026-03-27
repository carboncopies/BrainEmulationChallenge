#!/usr/bin/env python3
"""
Generate parameter grid search CSV for NETMORPH testing

Supports both single parameter sweeps and multi-parameter grid searches

Author: Varun Sinha  
Date: December 23, 2025

Usage:
    # Single parameter sweep
    ./generate_parameter_sweep.py --param all_axons.B_inf --lower 5 --upper 20 --steps 4
    
    # Multi-parameter grid search (tests ALL combinations)
    ./generate_parameter_sweep.py \
        --param1 all_axons.B_inf --lower1 5 --upper1 20 --steps1 3 \
        --param2 all_axons.growth_nu0 --lower2 0.0003 --upper2 0.0008 --steps2 2
    
    # Three parameters
    ./generate_parameter_sweep.py \
        --param1 all_axons.B_inf --lower1 5 --upper1 20 --steps1 3 \
        --param2 all_axons.growth_nu0 --lower2 0.0003 --upper2 0.0008 --steps2 2 \
        --param3 turn_separation --lower3 2 --upper3 4 --steps3 3
"""

import numpy as np
import pandas as pd
import argparse
import itertools

# Baseline values - used when not sweeping a parameter
BASELINE = {
    'all_axons.B_inf': 13.22,
    'all_axons.growth_nu0': 0.00052,
    'turn_separation': 5.0
}

VALID_PARAMS = ['all_axons.B_inf', 'all_axons.growth_nu0', 'turn_separation']

def generate_discrete_range(lower, upper, steps):
    """Generate evenly-spaced discrete values"""
    return np.linspace(lower, upper, steps)

def create_grid_search_csv(param_configs, output_file):
    """
    Create CSV that tests all combinations of parameters
    
    param_configs: list of dicts, each with:
        {'param': 'all_axons.B_inf', 'lower': 5, 'upper': 20, 'steps': 3}
    """
    print("\n" + "="*60)
    print("GRID SEARCH CONFIGURATION")
    print("="*60)
    
    # Generate values for each parameter
    param_ranges = {}
    for i, config in enumerate(param_configs, 1):
        param = config['param']
        values = generate_discrete_range(config['lower'], config['upper'], config['steps'])
        param_ranges[param] = values
        
        print(f"\nParameter {i}: {param}")
        print(f"  Range: {config['lower']} to {config['upper']}")
        print(f"  Steps: {config['steps']}")
        print(f"  Values: {values}")
    
    # Calculate total combinations
    total_tests = 1
    for values in param_ranges.values():
        total_tests *= len(values)
    
    print(f"\n{'='*60}")
    print(f"Total combinations to test: {total_tests}")
    print(f"Estimated time: ~{total_tests * 11} minutes ({total_tests * 11 / 60:.1f} hours)")
    print(f"{'='*60}\n")
    
    param_names = list(param_ranges.keys())
    value_lists = [param_ranges[p] for p in param_names]
    combinations = list(itertools.product(*value_lists))
    
    rows = []
    for test_id, combo in enumerate(combinations, 1):
        row = {
            'test_id': test_id,
            'all_axons.B_inf': BASELINE['all_axons.B_inf'],
            'all_axons.growth_nu0': BASELINE['all_axons.growth_nu0'],
            'turn_separation': BASELINE['turn_separation'],
            'convergent_neurons': '',
            'percentage': '',
            'status': '',
            'notes': ''
        }
        
        note_parts = []
        for param_name, value in zip(param_names, combo):
            row[param_name] = value
            note_parts.append(f"{param_name}={value:.6f}")
        
        row['notes'] = ", ".join(note_parts)
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)
    
    print(f"✓ Created {output_file} with {len(rows)} tests\n")
    print("Sample of generated combinations:")
    print(df.head(10).to_string(index=False))
    print(f"\n... and {len(rows) - 10} more tests" if len(rows) > 10 else "")
    
    print(f"\nRun tests with:")
    print(f"  ./test_parameter_combinations.py {output_file}\n")
    
    return df

def main():
    parser = argparse.ArgumentParser(
        description='Generate parameter sweep or grid search CSV for NETMORPH',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

Single Parameter Sweep:
  ./generate_parameter_sweep.py --param all_axons.B_inf --lower 5 --upper 20 --steps 4

Two-Parameter Grid Search (3 × 2 = 6 tests):
  ./generate_parameter_sweep.py \\
      --param1 all_axons.B_inf --lower1 5 --upper1 15 --steps1 3 \\
      --param2 all_axons.growth_nu0 --lower2 0.0003 --upper2 0.0008 --steps2 2

Three-Parameter Grid Search (3 × 2 × 3 = 18 tests):
  ./generate_parameter_sweep.py \\
      --param1 all_axons.B_inf --lower1 5 --upper1 15 --steps1 3 \\
      --param2 all_axons.growth_nu0 --lower2 0.0003 --upper2 0.0008 --steps2 2 \\
      --param3 turn_separation --lower3 2 --upper3 4 --steps3 3
        """
    )
    
    parser.add_argument('--param', choices=VALID_PARAMS,
                       help='Single parameter to sweep (old style)')
    parser.add_argument('--lower', type=float,
                       help='Lower bound for single parameter')
    parser.add_argument('--upper', type=float,
                       help='Upper bound for single parameter')
    parser.add_argument('--steps', type=int,
                       help='Number of steps for single parameter')
    
    for i in range(1, 4): 
        parser.add_argument(f'--param{i}', choices=VALID_PARAMS,
                           help=f'Parameter {i} for grid search')
        parser.add_argument(f'--lower{i}', type=float,
                           help=f'Lower bound for parameter {i}')
        parser.add_argument(f'--upper{i}', type=float,
                           help=f'Upper bound for parameter {i}')
        parser.add_argument(f'--steps{i}', type=int,
                           help=f'Number of steps for parameter {i}')
    
    parser.add_argument('--output', type=str, default='parameter_sweep.csv',
                       help='Output CSV filename (default: parameter_sweep.csv)')
    
    args = parser.parse_args()
    
    param_configs = []
    
    if args.param:
        if not all([args.lower is not None, args.upper is not None, args.steps]):
            print("Error: --param requires --lower, --upper, and --steps")
            return 1
        
        param_configs.append({
            'param': args.param,
            'lower': args.lower,
            'upper': args.upper,
            'steps': args.steps
        })
    
    for i in range(1, 4):
        param = getattr(args, f'param{i}')
        lower = getattr(args, f'lower{i}')
        upper = getattr(args, f'upper{i}')
        steps = getattr(args, f'steps{i}')
        
        if param:
            if not all([lower is not None, upper is not None, steps]):
                print(f"Error: --param{i} requires --lower{i}, --upper{i}, and --steps{i}")
                return 1
            
            param_configs.append({
                'param': param,
                'lower': lower,
                'upper': upper,
                'steps': steps
            })
    
    if not param_configs:
        print("Error: Must specify at least one parameter to sweep")
        print("Use --param or --param1, --param2, etc.")
        return 1
    
    for config in param_configs:
        if config['lower'] >= config['upper']:
            print(f"Error: lower bound must be less than upper bound for {config['param']}")
            return 1
        
        if config['steps'] < 2:
            print(f"Error: steps must be at least 2 for {config['param']}")
            return 1
    
    create_grid_search_csv(param_configs, args.output)
    
    return 0

if __name__ == "__main__":
    exit(main())
