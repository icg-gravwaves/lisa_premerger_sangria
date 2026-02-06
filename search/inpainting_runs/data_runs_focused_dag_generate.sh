#!/bin/bash

# Directories
repo_dir=/home/ian.harry/tmp_lisa_premerger_sangria_bug/lisa_premerger_sangria
run_dir=$repo_dir/search/inpainting_runs
result_dir=$run_dir/results_focused
log_dir=$run_dir/logs_focused
dag_file=$run_dir/sub_files_focused_dag/data_runs.dag

# Clear existing DAG file
rm -f $dag_file

# Create the result/log directories if they don't exist
mkdir -p $result_dir/out
mkdir -p $log_dir

psds="A:$repo_dir/estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt E:$repo_dir/estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt"

for end_time in $(seq 2638 3472) ; do
  seconds=$((end_time * 3600))
  job_name="job_$(printf "%09d" $seconds)"
  
  result_stem=$(printf "$result_dir/out/data_runs_%09d" $seconds)
  log_stem=$(printf "$log_dir/data_runs_%09d" $seconds)

  # Define the job in the DAG
  echo "JOB $job_name job.sub" >> $dag_file
  
  # Pass the variables to the template
  echo "VARS $job_name repo_dir=\"$repo_dir\" run_dir=\"$run_dir\" end_time_seconds=\"$seconds\" result_stem=\"$result_stem\" log_stem=\"$log_stem\"" psds=\"$psds\"" >> $dag_file
  
  # Optional: Retry jobs twice on failure
  echo "RETRY $job_name 2" >> $dag_file
done

echo "DAG file created at $dag_file"
echo "To submit: condor_submit_dag $dag_file"
