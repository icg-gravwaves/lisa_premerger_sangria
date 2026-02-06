set -e

for model in model estimate ; do
  python collect_data_results.py \
    --result-dir ./results/psd_$model/ \
    --output-file ./results/psd_$model/data_runs_results.hdf
done