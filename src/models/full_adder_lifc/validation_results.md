# Full Adder Validation Testing
**Tester:** Varun Sinha  
**Date:** October 14, 2025

## Test Performed
Validated full_adder_lifc.py produces correct outputs for all input combinations.

## Command
```bash
./full_adder_lifc.py -Host pve.braingenix.org -Port 8000
```

## Results
✓ All 7 test cases passed  
✓ See `home/skim/output/groundtruth-Vm.pdf` for voltage traces

## Validation Table

| Time (ms) | Cin | A | B | Expected Sum | Expected Cout | Status |
|-----------|-----|---|---|--------------|---------------|--------|
| 100 | 1 | 0 | 0 | 1 | 0 | ✓ Pass |
| 200 | 0 | 0 | 1 | 1 | 0 | ✓ Pass |
| 300 | 1 | 0 | 1 | 0 | 1 | ✓ Pass |
| 400 | 0 | 1 | 0 | 1 | 0 | ✓ Pass |
| 500 | 1 | 1 | 0 | 0 | 1 | ✓ Pass |
| 600 | 0 | 1 | 1 | 0 | 1 | ✓ Pass |
| 700 | 1 | 1 | 1 | 1 | 1 | ✓ Pass |
