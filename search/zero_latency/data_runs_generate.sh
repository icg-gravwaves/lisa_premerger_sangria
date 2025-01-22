set -e

repo_dir=/home/gareth.cabourndavies/lisa/lisa_premerger_sangria/
run_dir=$repo_dir/search/zero_latency

# Submission directory
sub_dir=$run_dir/sub_dir/

# We require 31 days of data for signal duration plus padding ; the first job (I think) will fail as we also need an extra hour be able to search for 1 hour before the merger

for psd_model in model estimate ; do
  result_dir=$run_dir/results/psd_${psd_model}/
  mkdir -p $result_dir
  log_dir=$run_dir/logs/psd_${psd_model}/
  mkdir -p $log_dir
  for remove in raw remove ; do
    dag_file=${sub_dir}/psd_${psd_model}_${remove}.dag
    rm -f ${dag_file}
    touch ${dag_file}
    for days_before_merger in 0.5 1 4 7 14 ; do
      echo $psd_model $remove $days_before_merger
      sanitize_dbm=`echo "$days_before_merger" | sed 's/\./p/g'`
      for end_time in $(seq $((31*24)) $((365*24))) ; do

        job_id=`printf "${sanitize_dbm}_%09d" $((end_time * 3600))`

        # set the naming of the out/log/err files
        mkdir -p $result_dir/${remove}/${sanitize_dbm}
        mkdir -p $log_dir/${remove}/${sanitize_dbm}

        result_stem=$result_dir/${remove}/${sanitize_dbm}/$job_id
        log_stem=$log_dir/${remove}/${sanitize_dbm}/$job_id

        # Define the job in the DAG
        echo "JOB $job_id job.sub" >> $dag_file
        if [[ "$remove" == "remove" ]] ; then
            remove_instruction="--remove-signals-after-coalescence -28800"
        else
            remove_instruction=""
        fi

        if [[ "$psd_model" == "estimate" ]] ; then
            psds="A:$repo_dir/estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt E:$repo_dir/estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt"
        else
            psds="A:$repo_dir/estimate_psds/model_AE_SMOOTHED_PSD.txt E:$repo_dir/estimate_psds/model_AE_SMOOTHED_PSD.txt"
        fi
        
        seconds=$(($end_time * 3600))

        # Pass the variables to the template
        echo "\
VARS $job_id \
repo_dir=\"$repo_dir\" \
run_dir=\"$run_dir\" \
end_time_seconds=\"$seconds\" \
result_stem=\"$result_stem\" \
log_stem=\"$log_stem\" \
remove_instruction=\"$remove_instruction\" \
days_before_merger=\"$days_before_merger\" \
psds=\"$psds\"" >> $dag_file
  
        echo "RETRY $job_id 2
        
        " >> $dag_file

      done
    done
  done
done
