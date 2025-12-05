set -e

result_file_inpaint=results/test_results_inpaint.txt

shared_args="""
  --psd-files \
    A:../../datasets/model_AE_TDI1_SMOOTH_optimistic.txt.gz \
    E:../../datasets/model_AE_TDI1_SMOOTH_optimistic.txt.gz \
  --f-lower 1e-6 \
  --data-file \
    ../../datasets/LDC2_sangria_hm_training.hdf \
  --reduce-bank-factor \
    3396 \
  --testing-plots results/test \
  --remove-signals-after-coalescence 1800 \
"""

# for signal, use 11440800 for inpainting, 11527200 for zerolag
# for noise, use 11345000 for inpainting, 11431400 for zerolag


python ./data_runs.py $shared_args \
  --bank-file \
    ../template_bank/output/lisa_ew_1_day.hdf \
  --days-to-search 21 \
  --time-points-days 0.5 1 4 7 14  \
  --time-point-window 3600 \
  --end-time 11440800  > ${result_file_inpaint}

shared_zerolag="--search-time 3600 --end-time 11527200"

for days_before in 14 7 4 1 0.5 ; do
  result_file_zerol=results/test_results_zero_latency_${days_before}.txt

  python ../signal_runs/data_runs.py \
    $shared_args $shared_zerolag \
    --bank-file \
      ../template_bank/output/lisa_ew_${days_before}_day.hdf \
    --days-before-merger ${days_before} > ${result_file_zerol}

done
