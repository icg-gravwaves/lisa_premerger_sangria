repo_dir=/home/gareth.cabourndavies/lisa_work/lisa_premerger_sangria/
run_dir=$repo_dir/search/zero_latency

sub_files=$run_dir/sub_files


for sub_file in `ls $sub_files/data_runs_remove_submit_14_only_*.sub` ; do
  condor_submit $sub_file
done