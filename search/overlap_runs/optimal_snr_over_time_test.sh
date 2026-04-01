repo_dir=/home/gareth.cabourndavies/lisa/lisa_premerger_sangria/
working_dir=$repo_dir/search/overlap_runs
python_exe=/home/gareth.cabourndavies/environments/env_lisa_premerger_sangria/bin/python

signal_number=5

$python_exe $working_dir/optimal_snr_over_time.py \
    --verbose \
    --psd-files \
        A:$repo_dir/estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt \
        E:$repo_dir/estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt \
    --f-lower 1e-6 \
    --data-file \
        $repo_dir/datasets/LDC2_sangria_hm_training.hdf \
    --output-plot-format \
        $working_dir/results/optimal_snr_over_time_{signal_no}_test.png \
    --output-file \
        $working_dir/results/optimal_snr_over_time_test.hdf \
    --signal-number $signal_number \
    --n-points 50 \
    --premerger-days 1 4 7 14