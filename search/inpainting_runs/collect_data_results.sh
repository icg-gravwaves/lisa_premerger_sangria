set -e

  python collect_data_results.py \
    --result-dir ./results/psd_inv_spectrum_truncation/out/ \
    --time-before 0.5 1 4 7 14 \
    --output-file ./results/data_runs_ist_results.hdf
