repo_dir=/home/gareth.cabourndavies/lisa_work/lisa_premerger_sangria/
working_dir=$repo_dir/search/overlap_runs
python_exe=/home/gareth.cabourndavies/environments/env_lisa_premerger/bin/python

rm optimal_snr_over_time.sub
for signal_number in {0..15} ; do
for log_xscale in "--log-xscale" "" ; do
echo """
executable=$python_exe
arguments = $working_dir/optimal_snr_over_time.py \
    --psd-files \
        A:$repo_dir/estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt \
        E:$repo_dir/estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt \
    --f-lower 1e-6 \
    --data-file \
        $repo_dir/datasets/LDC2_sangria_hm_training.hdf \
    --output-plot \
        $working_dir/results/optimal_snr_over_time_${signal_number}_$log_xscale.png \
    --signal-number $signal_number \
    --bank-files \
        0.5:$repo_dir/search/template_bank/lisa_ew_0.5_day_optimistic.hdf \
        1:$repo_dir/search/template_bank/lisa_ew_1_day_optimistic.hdf \
        4:$repo_dir/search/template_bank/lisa_ew_4_day_optimistic.hdf \
        7:$repo_dir/search/template_bank/lisa_ew_7_day_optimistic.hdf \
        14:$repo_dir/search/template_bank/lisa_ew_14_day_optimistic.hdf \
    --data-length 5184000 \
    --days-before 1 4 7 14 \
    $log_xscale

log = $working_dir/logs/optimal_snr_over_time_${signal_number}$log_xscale.log
output = $working_dir/logs/optimal_snr_over_time_${signal_number}$log_xscale.out
error = $working_dir/logs/optimal_snr_over_time_${signal_number}$log_xscale.err

request_memory = 4GB
request_cpus = 1
request_disk = 1GB

accounting_group = aluk.dev.o5.cbc.explore.test

queue
""" >> optimal_snr_over_time.sub

done
done