set -e

result_file_inpaint=results/test/test_results_inpaint.txt

mkdir -p results/test

shared_args="""
  --psd-files \
    A:../../datasets/model_AE_TDI1_SMOOTH_optimistic.txt.gz \
    E:../../datasets/model_AE_TDI1_SMOOTH_optimistic.txt.gz \
  --f-lower 1e-6 \
  --data-file \
    ../../datasets/LDC2_sangria_hm_training.hdf \
  --reduce-bank-factor \
    141808 \
  --testing-plots results/test \
  --remove-signals-after-coalescence 7200 \
"""

# for signal, use 11527200 for init_time
# for noise, use 26962425 for init_time

init_time=26962425

init_time_inpainting=$(($init_time - 86400))

python ./data_runs.py $shared_args \
  --verbose \
  --bank-file \
    ../template_bank/output/lisa_ew_1_day.hdf \
  --days-to-search 21 \
  --time-points-days 0.5 1 4 7 14  \
  --time-point-window 3600 \
  --end-time $init_time_inpainting  > ${result_file_inpaint}

shared_zerolag=" \
--search-time 3600 \
--end-time $init_time \
"

for days_before in 14 7 4 1 0.5 ; do
  result_file_zerol=results/test/test_results_zero_latency_${days_before}.txt

  python ../signal_runs/data_runs.py \
    $shared_args $shared_zerolag \
    --bank-file \
      ../template_bank/output/lisa_ew_1_day.hdf \
    --days-before-merger ${days_before} > ${result_file_zerol}

done
