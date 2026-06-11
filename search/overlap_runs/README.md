# Computing overlap between full signal and premerger signals

Peaks in the data were being produced when the data end was at the time of the merger. This was suspicious. We found that the cause was that the signals were so loud in the data, even the tiny overlap between the pre-merger truncated templates and the full-length signal could cause SNR spikes which peek out above the noise, and can be comparable to the true peak.

## Calculating signal overlap and fitting factors
To calculate the optimal SNR and fitting factor over time, we use `optimal_snr_over_time.py`.

```bash
python optimal_snr_over_time.py \
    --psd-files \
        A:$repo_dir/estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt \
        E:$repo_dir/estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt \
    --f-lower 1e-6 \
    --data-file \
        $repo_dir/datasets/LDC2_sangria_hm_training.hdf \
    --output-file \
        $working_dir/results/optimal_snr_over_time.hdf \
    --n-points 500 \
    --premerger-days 1 4 7 14
```

To perform these calculations, we loop through the signals and generate them using the FastTDI algorithm.

From here, we calculate the match for each of the premerger days given. This is done by looping through and cutting the signal at the appropriate time, then matching to the pre-merger waveform.

We then calculate the optimal SNR by matching the cut template to itself.

This was run on the head node in a loop using optima_snr_over_time.sh - probably not best practice but easy and straightforward.

We use the match to the signal template itself divided by the optimal SNR as a proxy for the fitting factor, this is to simplify calculations and avoid using matches to each template in the full template bank.

The next notebook shows the plots from these calculations for each of the signals in the Sangria-HM dataset. After that, we show the signals being removed from the data.