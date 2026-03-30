repo_dir=/home/gareth.cabourndavies/lisa/lisa_premerger_sangria/
banks_dir=$repo_dir/search/template_bank
python_exe=/home/gareth.cabourndavies/environments/env_lisa_premerger_sangria/bin/python

output_dir=$banks_dir/output
mkdir -p $output_dir
logs_dir=$banks_dir/logs
mkdir -p $logs_dir

for time_before in 0.5 1 4 7 14 ; do
    if [ $time_before = 0.5 ] ; then
      time_before_s=$((60 * 60 * 12))
    else
      time_before_s=$((60 * 60 * 24 * $time_before))
    fi
    echo "$time_before days before merger"
    echo $time_before_s
    echo """

    executable = $python_exe
    arguments = $banks_dir/pycbc_brute_bank --verbose \
      --minimal-match 0.97 \
      --tolerance .05 \
      --buffer-length 2592000 \
      --sample-rate .2 \
      --approximant BBHX_PhenomD \
      --tau0-threshold 100000 \
      --tau0-crawl 20000000 \
      --tau0-start 0 \
      --tau0-end  20000000 \
      --tau0-cutoff-frequency 0.0001 \
      --input-config config.ini \
      --seed 1 \
      --output-file $output_dir/lisa_ew_model_${time_before}_day.hdf \
      --time-before $time_before_s \
      --psd-file $repo_dir/estimate_psds/model_AE_SMOOTHED_PSD.txt \
      --low-frequency-cutoff .000001 

    output = $logs_dir/lisa_ew_model_${time_before}_day.out
    error = $logs_dir/lisa_ew_model_${time_before}_day.err
    log = $logs_dir/lisa_ew_model_${time_before}_day.log

    request_memory = 128GB
    request_cpus = 1
    request_disk = 1GB

    accounting_group = ligo.dev.o4.cbc.bbh.pycbcoffline
    queue
    """ > $logs_dir/lisa_ew_model_${time_before}_day.sub

    condor_submit $logs_dir/lisa_ew_model_${time_before}_day.sub
done