result_file_FIR=data_results_FIR.txt
result_file_inpaint=data_results_inpaint.txt

rm ${result_file_FIR}
rm ${result_file_inpaint}

touch ${result_file_FIR}
touch ${result_file_inpaint}

shared_args="""
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
    31 \
  --search-time 3600 \
  --reduce-bank-factor \
    50
"""


python ./data_runs.py $shared_args >> ${result_file_FIR}

python ./data_runs.py $shared_args --inpaint >> ${result_file_inpaint}


