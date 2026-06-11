# Inpainting Search Results

Now that we have explained how inpainting can be used as part of a pre-merger search, lets try it out.

Similar to the zero-latency filter search, we step through the data an hour at a time, we have a similar code (also called `data_runs.py`), but with some vital changes.


## Shared code / preprocessing

A lot of the code is shared between the two `data_runs.py` codes. Should this be in a common module? Probably, but if we changed it, we would want to rerun to test, and dont want to waste comput resources like that.

The code to load the data, subtract the mean, remove signals if needed etc. is all shared between the two codes. The only real differences are as follows:

### PSD generation
The PSDs do not have the zero-latency kernel applied, so we just load them straight from the data.

### Zero-padding
For inpainting, we pad the data with zeros at the end. This affects things like the frequency resolution of the PSD that is needed.

## Loop through bank waveforms
This loop is very similar. The waveform is loaded from the bank and passed to a SNR series function. For inpainting though, we have a loop over the days-before-merger points that we want to consider (`--time-points-days`). For each of these, we compare to the best SNR that has come before and update as appropriate.

# Running the analysis
The data_runs.py code can be run using
```bash
python ./data_runs.py \
  --psd-files \
    A:../../estimate_psds/model_AE_SMOOTHED_PSD.txt \
    E:../../estimate_psds/model_AE_SMOOTHED_PSD.txt \
  --f-lower 1e-6 \
  --data-file \
    ../../datasets/LDC2_sangria_hm_training.hdf \
  --bank-file \
    ../template_bank/output/lisa_ew_1_day.hdf \
  --days-to-search 21 \
  --time-points-days 0.5 1 4 7 14  \
  --time-point-window 3600 \
  --end-time $init_time
```

Again, for testing, we have the options `--testing-plots` and `--reduce-bank-factor`. These options produce plots in the given directory, or decimate the templates used by the factor given.

## Submitting jobs
For production runs, similar to the zero-latency case, we generate a dag file with `data_runs_generate.sh` and use `job.sub` as the template that values are added to.

## Result collection
Each analysis then covers an hour and results are saved in a text file. These text files are then scraped using `collect_data_results.py` and added to a single file. This is included in the repository under `search/inpainting/results/data_runs_psd_{estimate,model}.hdf`, where the values in curly brackets indicate the choice of PSD model.

Comparing to the zero-latency filter runs, we always use pre-merger removal, with default of 2 hours, but variable values in the region where signals are desnsely-packed, as discussed later.

Next we compare zero-latency filter and inpainting SNR outputs using the functions defined so that we are confident that they match what we have developed.