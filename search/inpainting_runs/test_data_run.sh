set -e

result_file_inpaint=results/test_results_inpaint.txt
result_file_zerol=results/test_results_zero_latency.txt

shared_args="""
  --psd-files \
    A:../../datasets/model_AE_TDI1_SMOOTH_optimistic.txt.gz \
    E:../../datasets/model_AE_TDI1_SMOOTH_optimistic.txt.gz \
  --f-lower 1e-6 \
  --bank-file \
    ../template_bank/output/lisa_ew_1_day.hdf \
  --data-file \
    ../../datasets/LDC2_sangria_hm_training.hdf \
  --reduce-bank-factor \
    3396 \
  --remove-signals-after-coalescence \
    3600 \
  --testing-plots results/test \
"""


python ./data_runs.py $shared_args \
  --days-before-merger 1 \
  --search-time 7200 \
  --end-time 11527200  > ${result_file_inpaint}

python ../signal_runs/data_runs.py $shared_args \
  --days-before-merger 1 \
  --search-time 7200 \
  --end-time 11527200 > ${result_file_zerol}
