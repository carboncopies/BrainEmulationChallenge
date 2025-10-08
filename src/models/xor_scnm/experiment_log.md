# NETMORPH Parameter Tuning Experiments - XOR Reservoir
**Date:** October 2, 2025
**Parameter Tested:** all_axons.B_inf (expected number of axon branching events)

## Baseline Configuration
- **B_inf:** 13.21658
- **Total connections:** 262
- **PyrMid convergent neurons:** 5 [5,7,8,9,13]
- **XOR pathways found:** Yes (8 final connections)

## Experiment 1: Moderate Increase
- **B_inf:** 15.0 (+13.5%)
- **Total connections:** 267 (+5, +1.9%)
- **PyrMid convergent neurons:** 5 [6,7,8,13,14]
- **XOR pathways found:** Yes (8 final connections)

## Experiment 2: High Increase
- **B_inf:** 18.0 (+36%)
- **Total connections:** 271 (+9, +3.4%)
- **PyrMid convergent neurons:** 8 [5,7,8,9,10,11,13,14]
- **XOR pathways found:** Yes (8 final connections)

## Experiment 3: Low Decrease
- **B_inf:** 10.0 (-24%)
- **Total connections:** 256 (-6, -2.3%)
- **PyrMid convergent neurons:** 9 [5,6,7,8,10,11,12,13,14]
- **XOR pathways found:** Yes (8 final connections)

## Summary Table
| Experiment | B_inf | Total Connections | PyrMid Convergent Neurons |
|------------|-------|-------------------|---------------------------|
| Low | 10.0 | 256 | 9 |
| Baseline | 13.22 | 262 | 5 |
| Moderate | 15.0 | 267 | 5 |
| High | 18.0 | 271 | 8 |

---

# Elongation Rate Parameter Sweep
**Date:** October 2, 2025
**Parameter Tested:** all_axons.growth_nu0 (axon elongation rate in μm/s)
**Note:** B_inf restored to baseline (13.21658) for this sweep

## Baseline Configuration
- **growth_nu0:** 0.0005208333 (~45 μm/day)
- **Total connections:** 262
- **PyrMid convergent neurons:** 5 [5,7,8,9,13]
- **XOR pathways found:** Yes (8 final connections)

## Experiment 4: Low Elongation Rate
- **growth_nu0:** 0.0003 (-42%, ~26 μm/day)
- **Total connections:** 116 (53 usable)
- **PyrMid convergent neurons:** 0 (NONE)
- **XOR pathways found:** No - failed
- **Result:** Axons grew too slowly to reach from PyrIn to PyrMid layer. No convergent neurons formed.

## Experiment 5: High Elongation Rate
- **growth_nu0:** 0.0008 (+54%, ~69 μm/day)
- **Total connections:** 324
- **PyrMid convergent neurons:** 10 [5,6,7,8,9,10,11,12,13,14] (ALL)
- **XOR pathways found:** Yes (8 final connections)
- **Result:** All PyrMid neurons receive convergent input. Best connectivity achieved

## turn_separation Parameter (Turning Frequency)

**Baseline**
- turn_separation: 5.0
- Total connections: 262
- Convergent neurons: 5

**Experiment 6: Straighter Paths**
- turn_separation: 10.0 (+100%, turns less often)
- Total connections: 201
- Convergent neurons: 7
- XOR pathways found: Yes (8 final connections)
- Result: Fewer total connections but more convergent neurons than baseline

**Experiment 7: More Wandering Paths**=
- turn_separation: 2.5 (-50%, turns more often)
- Total connections: 306
- Convergent neurons: 8 [5,7,8,9,10,11,13,14]
- XOR pathways found: Yes (8 final connections)
- Result: Best result for turn_separation - more wandering improved connectivity

---

## E Parameter (Competition for Resources)

**Baseline**
- E: 0.319251
- Total connections: 262
- Convergent neurons: 5

**Experiment 8: Low Competition**
- E: 0.2 (-37%, less competition)
- Total connections: 296
- Convergent neurons: 9
- XOR pathways found: Yes
- Result: Best result - less competition allowed more convergent connections

**Experiment 9: High Competition**
- E: 0.5 (+57%, more competition)
- Total connections: 234
- Convergent neurons: 7
- XOR pathways found: Yes
- Result: More competition reduced both total and convergent connections
