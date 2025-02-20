result_file=data_results.txt

rm ${result_file}
touch ${result_file}

for end_time in $(seq $((47*24)) $((62*24))) ; do
echo $((end_time * 3600)) >> ${result_file}
python ./data_runs.py \
  --days-before-merger \
    1 \
  --psd-files \
    A:../../estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt \
    E:../../estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt \
  --f-lower 1e-6 \
  --bank-file \
    /home/gareth/lisa/lisa_early_warning/lisa_premerger_paper/Search/Template_Banks/lisa_ew_1_day_optimistic.hdf \
  --data-file \
    ../../datasets/LDC2_sangria_hm_training.hdf \
  --end-time \
    $(($end_time * 3600)) \
  --search-time 3600 \
  --reduce-bank-factor \
    50 >> ${result_file}

done