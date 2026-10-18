# Supplementary validation report

## Checks

- external_manifest_rows=90 families=30
- open_set_manifest_rows=120 labels={'positive_in_scope': 60, 'negative_out_of_scope': 60} negative_groups={'candidate_out_fern': 15, 'angiosperm': 15, 'gymnosperm_cycad': 15, 'bryophyte_liverwort': 15}
- raw_order: rows=540 success=540 errors=0 expected_final_rows=540
- raw_external: rows=270 success=270 errors=0 expected_final_rows=270
- raw_open: rows=360 success=360 errors=0 expected_final_rows=360
- STATE dashscope-qwen35-flash__qwen3.5-flash__external_validation_direct30_90.state.json: completed 90/90 next=None
- STATE dashscope-qwen35-flash__qwen3.5-flash__open_set_120.state.json: completed 120/120 next=None
- STATE dashscope-qwen35-flash__qwen3.5-flash__order_seed_20260512_direct30_masked60.state.json: completed 60/60 next=None
- STATE dashscope-qwen35-flash__qwen3.5-flash__order_seed_20260513_direct30_masked60.state.json: completed 60/60 next=None
- STATE dashscope-qwen35-flash__qwen3.5-flash__order_seed_20260514_direct30_masked60.state.json: completed 60/60 next=None
- STATE dashscope-qwen397b__qwen3.5-397b-a17b__external_validation_direct30_90.state.json: completed 90/90 next=None
- STATE dashscope-qwen397b__qwen3.5-397b-a17b__open_set_120.state.json: completed 120/120 next=None
- STATE dashscope-qwen397b__qwen3.5-397b-a17b__order_seed_20260512_direct30_masked60.state.json: completed 60/60 next=None
- STATE dashscope-qwen397b__qwen3.5-397b-a17b__order_seed_20260513_direct30_masked60.state.json: completed 60/60 next=None
- STATE dashscope-qwen397b__qwen3.5-397b-a17b__order_seed_20260514_direct30_masked60.state.json: completed 60/60 next=None
- STATE google-gemini__gemini-3.1-flash-lite__external_validation_direct30_90.state.json: completed 90/90 next=None
- STATE google-gemini__gemini-3.1-flash-lite__open_set_120.state.json: completed 120/120 next=None
- STATE google-gemini__gemini-3.1-flash-lite__order_seed_20260512_direct30_masked60.state.json: completed 60/60 next=None
- STATE google-gemini__gemini-3.1-flash-lite__order_seed_20260513_direct30_masked60.state.json: completed 60/60 next=None
- STATE google-gemini__gemini-3.1-flash-lite__order_seed_20260514_direct30_masked60.state.json: completed 60/60 next=None
- CSV_READABLE confidence_bins.csv: 77 rows
- CSV_READABLE confidence_calibration_summary.csv: 15 rows
- CSV_READABLE error_taxonomy_cases.csv: 858 rows
- CSV_READABLE error_taxonomy_summary.csv: 89 rows
- CSV_READABLE external_validation_per_family.csv: 90 rows
- CSV_READABLE external_validation_summary.csv: 3 rows
- CSV_READABLE genus_level_summary.csv: 5 rows
- CSV_READABLE high_confidence_errors.csv: 665 rows
- CSV_READABLE macro_balanced_summary.csv: 15 rows
- CSV_READABLE open_set_false_positive_cases.csv: 23 rows
- CSV_READABLE open_set_rejection_summary.csv: 3 rows
- CSV_READABLE open_set_retention_positive_cases.csv: 180 rows
- CSV_READABLE order_position_bias.csv: 170 rows
- CSV_READABLE order_prediction_consistency.csv: 9 rows
- CSV_READABLE order_prediction_entropy.csv: 180 rows
- CSV_READABLE order_robustness_summary.csv: 9 rows
- CSV_READABLE per_family_performance.csv: 450 rows
- CSV_READABLE species_to_genus_error_cases.csv: 191 rows
- CSV_READABLE supplementary_master_summary.csv: 50 rows
- CSV_READABLE supplementary_pairwise_mcnemar_bootstrap.csv: 21 rows

## Status

All planned supplementary experiment artifacts are complete.
