set -e

for days_before in 0.5 1 4 7 14  ; do

  python collect_data_results.py \
    --result-dir ./results/${days_before} \
    --exclude-string remove \
    --require-string raw \
    --output-file ./results/data_runs_raw_${days_before}_results.hdf

  python collect_data_results.py \
    --result-dir ./results/${days_before} \
    --require-string remove \
    --exclude-string raw \
    --output-file ./results/data_runs_remove_${days_before}_results.hdf

done