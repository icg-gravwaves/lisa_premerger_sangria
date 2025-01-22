set -e

for model in model estimate ; do
  echo "full data $model"
  python collect_data_results.py \
    --verbose \
    --n-times 324 \
    --result-dir ./results/psd_${model}/ \
    --output-file ./results/data_runs_psd_${model}.hdf
done

for removal in noremoval varied_removal ; do
  echo "focused $removal"
  python collect_data_results.py \
    --verbose \
    --n-times 324 \
    --result-dir ./results/focused_results_${removal} \
    --output-file results/data_runs_focused_${removal}.hdf
done

echo "Signal 0 gaps"
python collect_data_results.py \
  --verbose \
  --n-times 324 \
  --result-dir ./results/signal_0_gaps \
  --output-file results/data_runs_signal_0_gaps.hdf