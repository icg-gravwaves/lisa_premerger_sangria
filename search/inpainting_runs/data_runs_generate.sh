set -e

repo_dir=/home/gareth.cabourndavies/lisa/lisa_premerger_sangria/
run_dir=$repo_dir/search/inpainting_runs

# Submission directory
sub_dir=$run_dir/sub_dir/

# We require 31 days of data for signal duration plus padding ; the first job (I think) will fail as we also need an extra hour be able to search for 1 hour before the merger

for psd_model in model estimate ; do
  result_dir=$run_dir/results/psd_${psd_model}/
  mkdir -p $result_dir
  log_dir=$run_dir/logs/psd_${psd_model}/
  mkdir -p $log_dir

  dag_file=${sub_dir}/psd_${psd_model}.dag
  rm -f ${dag_file}*
  touch ${dag_file}
  echo $psd_model
  for end_time in $(seq $((31*24)) $((365*24))) ; do

    job_id=`printf "%09d" $((end_time * 3600))`

    result_stem=$result_dir/$job_id
    log_stem=$log_dir/$job_id

    if [[ "$psd_model" == "estimate" ]] ; then
        psds="A:$repo_dir/estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt E:$repo_dir/estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt"
    else
        psds="A:$repo_dir/datasets/model_AE_TDI1_SMOOTH_optimistic.txt.gz E:$repo_dir/datasets/model_AE_TDI1_SMOOTH_optimistic.txt.gz"
    fi
    
    seconds=$(($end_time * 3600))
    # Define the job in the DAG
    echo "JOB $job_id job.sub" >> $dag_file
  
      # Pass the variables to the template
    echo "\
VARS $job_id \
repo_dir=\"$repo_dir\" \
run_dir=\"$run_dir\" \
end_time_seconds=\"$seconds\" \
result_stem=\"$result_stem\" \
log_stem=\"$log_stem\" \
psds=\"$psds\"" >> $dag_file

    echo "RETRY $job_id 2
    
    " >> $dag_file

  done
done
