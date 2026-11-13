# Interneuron dendrite rerun (own NES 8000/8001), 2026-11-12/13
Scripts: grow_dend.py (driver, one run per process, no wrapper timeout so client is never killed), analyze_dend.py. Data: dend_results.json. Run folders grow_S1..S3.
Common: seed 20240628, 96 pyr, days 25, D_synmax pyr.pyr 1.5, int pairs 0.1, axon block restated as R1 (B_inf 26, tau 1681541, E .319251, min_node_interval 0), dendrite block restated (van_Pelt, tau 259680, E 0.73, min_node_interval 2.0; default B_inf 2.52).
S1: 48 int, basal 6-10, dend B_inf 3.5. S2: 48 int, basal 4-8, dend B_inf 5. S3: 16 int, basal 6-10, dend B_inf 3.5.
Directives confirmed in each _report (axon B_inf=26.00, dendrite B_inf=3.50/5.00, min_node_interval as above). bio_check passed for all. Models saved v2-arbor-S10000/S20000/S30000. Sims 136-138 deleted (run.log "Deleted resident simulation"; GetStatus on 135-140 returns StatusCode 2 = not found).
See dend_results.json for numbers. Pyr->Pyr change is vs R0 (73697).
