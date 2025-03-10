repo_dir=/home/gareth.cabourndavies/lisa_work/lisa_premerger_sangria/
run_dir=$repo_dir/search/signal_runs
result_dir=$run_dir/results

sub_files=$run_dir/sub_files

rm ${sub_files}/*
rm ${result_dir}/*

job_counter=0

# We require 31 days of data for signal duration plus padding ; the first job will fail as we also need an extra hour be able to search for 1 hour before the merger

for end_time in $(seq $((31*24)) $((350*24))) ; do
job_counter=$((job_counter+1))
subfile_counter=$((job_counter/100))

sub_file=`printf "${sub_files}/data_runs_submit_%03d.sub" $subfile_counter`
echo "# $((end_time * 3600))" >> ${sub_file}
result_stem=`printf "$result_dir/data_runs_%09d" $((end_time * 3600))`
echo $sub_file
echo $result_stem
echo """
executable = /home/gareth.cabourndavies/environments/env_lisa_premerger/bin/python
arguments = $run_dir/data_runs.py \
  --days-before-merger 1 \
  --psd-files \
    A:$repo_dir/estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt \
    E:$repo_dir/estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt \
  --f-lower 1e-6 \
  --bank-file \
    $repo_dir/search/template_bank/lisa_ew_1_day_optimistic.hdf \
  --data-file \
    $repo_dir/datasets/LDC2_sangria_hm_training.hdf \
  --end-time \
    $(($end_time * 3600)) \
  --search-time 3600 \
  --reduce-bank-factor \
    50


output = $result_stem.out
error = $result_stem.err
log = $result_stem.log

request_memory = 4GB
request_cpus = 1
request_disk = 1GB

accounting_group = aluk.dev.o5.cbc.pycbcoffline
queue
""" >> ${sub_file}
done

for sub_file in `ls $sub_files` ; do
  condor_submit $sub_files/$sub_file
done