set -e

result_file_inpaint=results/test_results_inpaint.txt
result_file_zerol=results/test_results_zero_latency.txt

shared_args="""
  --days-before-merger \
    1 \
  --psd-files \
    A:../../datasets/model_AE_TDI1_SMOOTH_optimistic.txt.gz \
    E:../../datasets/model_AE_TDI1_SMOOTH_optimistic.txt.gz \
  --f-lower 1e-6 \
  --bank-file \
    ../../datasets/lisa_ew_1_day_optimistic.hdf \
  --data-file \
    ../../datasets/LDC2_sangria_hm_training.hdf \
  --end-time \
    11528700 \
  --search-time 3600 \
  --reduce-bank-factor \
    100 \
  --remove-signals-after-coalescence \
    43200
"""


# python ./data_runs.py $shared_args > ${result_file_inpaint}
python ../signal_runs/data_runs.py $shared_args > ${result_file_zerol}
