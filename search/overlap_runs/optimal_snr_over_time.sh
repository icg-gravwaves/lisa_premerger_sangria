repo_dir=/home/gareth.cabourndavies/lisa_work/lisa_premerger_sangria/
working_dir=$repo_dir/search/overlap_runs
python_exe=/home/gareth.cabourndavies/environments/env_lisa_premerger_sangria/bin/python

mkdir -p sub_files
rm sub_files/optimal_snr_over_time.sub
touch sub_files/optimal_snr_over_time.sub
for signal_number in {0..14} ; do
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
        $working_dir/results/optimal_snr_over_time_${signal_number}.png \
    --output-file \
        $working_dir/results/optimal_snr_over_time_${signal_number}.hdf \
    --signal-number $signal_number \
    --data-length 5184000

log = $working_dir/logs/optimal_snr_over_time_${signal_number}.log
output = $working_dir/logs/optimal_snr_over_time_${signal_number}.out
error = $working_dir/logs/optimal_snr_over_time_${signal_number}.err

request_memory = 4GB
request_cpus = 1
request_disk = 1GB

accounting_group = ligo.dev.o4.cbc.bbh.pycbcoffline

queue
""" >> sub_files/optimal_snr_over_time.sub

done