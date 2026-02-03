repo_dir=/home/gareth.cabourndavies/lisa/lisa_premerger_sangria/
run_dir=$repo_dir/search/zero_latency

dag_file=$run_dir/sub_dir/psd_estimate/psd_estimate.dag

if [ ! -f "$dag_file" ]; then
  echo "DAG file not found: $dag_file"
  exit 1
fi

echo "Submitting DAG: $dag_file"
condor_submit_dag -f "$dag_file"
