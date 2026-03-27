# NETMORPH Parameter Optimization

Author: Varun Sinha  
Date: December 2025  
Confluence: https://carboncopiespythondev.atlassian.net/wiki/spaces/PCD/pages/35356687/Fall+2025+internship+Netmorph+development

## Overview

Tools for optimizing NETMORPH parameters for XOR circuit generation using Bayesian optimization and grid search validation.

## Files

- `bayesian_optimization.py` - Gaussian Process-based parameter optimization
- `generate_parameter_sweep.py` - Generates grid search parameter combinations
- `test_parameter_combinations.py` - Executes grid search tests
- `bayesian_optimization_results.csv` - Results from 40 Bayesian optimization tests
- `parameter_sweep_results.csv` - Results from 18 grid search validation tests

## Usage

### Bayesian Optimization

**Inputs:**
- Parameter ranges (B_inf, growth_nu0, turn_separation)
- Number of tests (--n-calls)
- Number of random initial tests (--n-initial)

**Command:**
```bash
./bayesian_optimization.py --n-calls 30 --n-initial 5
```

**Expected Outputs:**
- `bayesian_optimization_results.csv` - Test results with convergent neuron counts
- `bayesian_logs/` - Individual test logs for each run

### Grid Search

**Inputs:**
- Parameter ranges and step sizes for each parameter
- Generated CSV with parameter combinations

**Command:**
```bash
# Generate parameter grid
./generate_parameter_sweep.py \
    --param1 all_axons.B_inf --lower1 6 --upper1 20 --steps1 3 \
    --param2 all_axons.growth_nu0 --lower2 0.00075 --upper2 0.0008 --steps2 2 \
    --param3 turn_separation --lower3 3.0 --upper3 8.0 --steps3 3

# Run tests
./test_parameter_combinations.py parameter_sweep.csv
```

**Expected Outputs:**
- `parameter_sweep.csv` - Generated parameter combinations
- `parameter_sweep_results.csv` - Test results for each combination

## Results Summary

Bayesian optimization discovered two optimal parameter regions:
- Low B_inf (6.0): 100% success rate, parameter-sensitive
- High B_inf (20.0): 83% success rate, robust across turn_separation values

Recommended: B_inf=20.0, growth_nu0=0.0008 for most robust performance
