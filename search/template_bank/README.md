# Template Banks

For the template banks, as in [our previous work](https://arxiv.org/abs/2411.07020), we use a stochastic placement algorithm.

We use the same modified version of `pycbc_brute_bank`, this is included oin our repo for ease of use, but:

```bash
 $ wget https://github.com/icg-gravwaves/lisa_premerger_paper/raw/refs/heads/main/Search/Template_Banks/pycbc_brute_bank 
 # (Downloads as pycbc_brute_bank.1)

 $ diff pycbc_brute_bank pycbc_brute_bank.1
 #produces no output
```

This was then run using the folllowing:

```bash
repo_dir= #replace with your own repository directory
banks_dir=$repo_dir/search/template_bank
python_exe= #use `which python` with your conda environment activated to fine the python executable location

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
      --output-file $output_dir/lisa_ew_${time_before}_day.hdf \
      --time-before $time_before_s \
      --psd-file $repo_dir/estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt \
      --low-frequency-cutoff .000001

    output = $logs_dir/lisa_ew_${time_before}_day.out
    error = $logs_dir/lisa_ew_${time_before}_day.err
    log = $logs_dir/lisa_ew_${time_before}_day.log

    request_memory = 128GB
    request_cpus = 1
    request_disk = 1GB

    queue
    """ > $logs_dir/lisa_ew_${time_before}_day.sub

    condor_submit $logs_dir/lisa_ew_${time_before}_day.sub
done
```

This generated and submitted condor jobs for bank generation for each day before merger.

Your local computing setup may require additional information; accounting groups, memory / disk / cpu number request etc., which you will need to add yourself.

The `--psd-file` option was replaced as appropriate for the PSD model file.