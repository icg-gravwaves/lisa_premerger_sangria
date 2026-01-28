repo_dir=/home/gareth.cabourndavies/lisa_work/lisa_premerger_sangria/
run_dir=$repo_dir/search/zero_latency
result_dir=$run_dir/results
log_dir=$run_dir/logs

sub_files=$run_dir/sub_files

rm ${sub_files}/data_runs_submit_*

job_counter=0

# We require 31 days of data for signal duration plus padding ; the first job (I think) will fail as we also need an extra hour be able to search for 1 hour before the merger

for days_before_merger in 0.5 1 4 7 14 ; do
  # Make sure the days before directory exists
  mkdir -p $log_dir/${days_before_merger}
  mkdir -p $result_dir/${days_before_merger}
  for remove in raw remove ; do
    for end_time in $(seq $((31*24)) $((365*24))) ; do
      job_counter=$((job_counter+1))
      subfile_counter=$((job_counter/500))

      sub_file=`printf "${sub_files}/data_runs_submit_%03d.sub" $subfile_counter`
      echo "# $days_before_merger, $remove, $((end_time * 3600))" >> ${sub_file}
      result_stem=`printf "$result_dir/${days_before_merger}/data_runs_${remove}_${days_before_merger}_%09d" $((end_time * 3600))`
      log_stem=`printf "$log_dir/${days_before_merger}/data_runs_${remove}_${days_before_merger}_%09d" $((end_time * 3600))`
      echo $sub_file
      echo $result_stem
      if [[ "$remove" == "remove" ]] ; then
        remove_instruction="--remove-signals-after-coalescence 1800"
      else
        remove_instruction=""
      fi
      echo """
      executable = /home/gareth.cabourndavies/environments/env_lisa_premerger/bin/python
      arguments = $run_dir/data_runs.py \
        --days-before-merger ${days_before_merger} \
        --psd-files \
          A:$repo_dir/estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt \
          E:$repo_dir/estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt \
        --f-lower 1e-6 \
        --bank-file \
          $repo_dir/search/template_bank/output/lisa_ew_${days_before_merger}_day.hdf \
        --data-file \
          $repo_dir/datasets/LDC2_sangria_hm_training.hdf \
        --end-time \
          $(($end_time * 3600)) \
        --search-time 3600 \
        $remove_instruction


      output = $result_stem.out
      error = $log_stem.err
      log = $log_stem.log

      request_memory = 4GB
      request_cpus = 1
      request_disk = 1GB

      accounting_group = aluk.dev.o4.cbc.pycbcoffline
      queue
      """ >> ${sub_file}
    done
  done
done

