set -e

repo_dir=/home/gareth.cabourndavies/lisa/lisa_premerger_sangria/
run_dir=$repo_dir/search/zero_latency
result_dir=$run_dir/results/psd_estimate/
mkdir -p $result_dir
log_dir=$run_dir/logs/psd_estimate
mkdir -p $log_dir

sub_dir=$run_dir/sub_dir/psd_estimate/
mkdir -p $sub_dir

# clean previous submit files and dag
rm -f ${sub_dir}/submit_*.sub
rm -f ${sub_dir}/psd_estimate.dag


# We require 31 days of data for signal duration plus padding ; the first job (I think) will fail as we also need an extra hour be able to search for 1 hour before the merger

for days_before_merger in 0.5 1 4 7 14 ; do
  # Make sure the days before directory exists
  mkdir -p $log_dir/${days_before_merger}
  mkdir -p $result_dir/${days_before_merger}
  for remove in raw remove ; do
    for end_time in $(seq $((31*24)) $((365*24))) ; do

  job_id=`printf "%09d" $((end_time * 3600))`

  # create one submit file per job using the same naming as the out/log/err files
  mkdir -p ${sub_dir}/${remove}/${days_before_merger}
  mkdir -p $result_dir/${remove}/${days_before_merger}
  mkdir -p $log_dir/${remove}/${days_before_merger}

  sub_file=${sub_dir}/${remove}/${days_before_merger}/submit_$job_id.sub
  # write a comment header for easier debugging
  echo "# $days_before_merger, $remove, $job_id" > ${sub_file}
  result_stem=$result_dir/${remove}/${days_before_merger}/$job_id
  log_stem=$log_dir/${remove}/${days_before_merger}/$job_id
  echo $sub_file
  echo $result_stem
      if [[ "$remove" == "remove" ]] ; then
        remove_instruction="--remove-signals-after-coalescence 1800"
      else
        remove_instruction=""
      fi
      cat >> ${sub_file} <<EOF
executable = /home/gareth.cabourndavies/environments/env_lisa_premerger_sangria/bin/python
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

accounting_group = ligo.dev.o5.cbc.bbh.pycbcoffline
environment = "PATH=/home/gareth.cabourndavies/environments/env_lisa_premerger_sangria/bin:\$(PATH);PYTHONHOME=/home/gareth.cabourndavies/environments/env_lisa_premerger_sangria"
getenv = True
queue
EOF

  # add this job to the DAG file; node names must be safe (no dots)
  dbm_sanitized=$(echo ${days_before_merger} | tr '.' 'p')
  node_name="psd_estimate_${remove}_${dbm_sanitized}_$job_id"
  echo "JOB $node_name $sub_file" >> ${sub_dir}/psd_estimate.dag
    done
  done
done

