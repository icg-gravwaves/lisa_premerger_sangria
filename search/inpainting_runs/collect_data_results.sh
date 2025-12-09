set -e

  python collect_data_results.py \
    --result-dir ./results/out/ \
    --time-before 0.5 1 4 7 14 \
    --output-file ./results/data_runs_results.hdf
