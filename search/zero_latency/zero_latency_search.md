# Zero Latency Searches

We have the PSDs and the banks - lets go!

Most of the following is in `data_runs.py`, but as we later move to a different search, many of the shared utilities have been added to [common_utils.py](../common_utils.py). As a result, it can be a little hard to follow what is happening in just the main code, but lets go through it step-by-step.

## Loading the data

The Sangria-HM data is the full two years of flight for LISA. We need to slice the data so that we effectively see an end to the data, and walk that slice through the data hour-by-hour. 
This can produce duplicates around the edges, e.g. seeing a peak at 3595s could then have a similar value at 0s in the next stride, but we ignore that for now.

The data is loaded from the data file and converted to AET channels. The start / end indices are calculated and the slice is taken.

We then have options for removing signals from the data - this will be covered more later.

The mean is subtracted, which helps remove some strange behaviour we saw with a zero-frequency offset in the predicted SNR timeseries. This mattered more in the inpainting search, but it is included here as well for consistency.

## PSD and data conditioning
We then generate the PSD objects - these are where the zero-lateency filter comes in, so we use a wrapper around the usual PyCBC PSD loading routines.

We apply the routine to pre-process the data - this is largely zero padding and tapering so that we don't get weird edge effects.

## Loop through the bank
We loop through the bank and calculate the SNR. This uses a function `get_snr_from_series` which is in the utils module, which gets the maximum SNR in the final X seconds of the series (we used 3600).

If the SNR is higher than the maximum in any tempate so far, then the trigger and template information are kept.

# Running the analysis
To run the analysis, we loop through the times needed in bash, and use these when calling data_runs.py.

```bash
python ../zero_latency/data_runs.py \
    --psd-files \
        A:../../estimate_psds/model_AE_SMOOTHED_PSD.txt \
        E:../../estimate_psds/model_AE_SMOOTHED_PSD.txt \
    --f-lower 1e-6 \
    --data-file \
        ../../datasets/LDC2_sangria_hm_training.hdf \
    --days-before-merger 14 \
    --search-time 3600 \
    --end-time $init_time \

```

For testing, we have the options `--testing-plots` and `--reduce-bank-factor`. These options produce plots in the given directory, or decimate the templates used by the factor given.

## Submitting jobs
The scripts were run using a condor dag file, generated through `data_runs_generate.sh`, and which used a template job submit file in `job.sub`. These contain specific instructions for the cluster we ran on, so these will probably need edited for your own version.

## Result collection
Each analysis then covers an hour and results are saved in a text file. These text files are then scraped using `collect_data_results.py` and added to a single file. This is included in the repository under `search/zero_latency/results/psd_{estimate,model}/data_runs_raw_{0.5,1,4,7,14}.hdf`, where the values in curly brackets indicate the choice of PSD model and `--days-before-merger` respectively.


We then saw an issue: there were peaks being produced at the time of the merger, predicting a signal days-before-merger later.