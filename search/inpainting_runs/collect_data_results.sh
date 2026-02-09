set -e

for model in model estimate ; do
  python collect_data_results.py \
    --verbose \
    --n-times 324 \
    --result-dir ./results/psd_${model}/ \
    --output-file ./results/data_runs_psd_${model}.hdf
done