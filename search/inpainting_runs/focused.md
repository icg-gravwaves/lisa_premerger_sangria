# Focused region - overlapping signals

Looking at the results in the previous notebook, we see that signals 2-5 overlap dramatically throughout the analysis.

This won't really be a problem. This comes from using a uniform pre-merger signal removal time of 2 hours. Lets apply some more realistic signal removal choices, and remove signals as the get to the SNR ~10 threshold.

## Running the analysis
We re-ran `data-runs.py`, but with either no removal, or variable times-before-merger for the cutoff, particularly using 11 days premerger for Signal 3 and 14 days premerger for signal 4. We probably could have done more than 14 days premerger for Signal 4, but thats only what we did the analysis up to.

This was run using `data_runs_focused_dag_generate.sh` to generate a dag file, using `job.sub` as the template once again. Data results were collected using

```bash
for removal in noremoval varied_removal ; do
  echo "focused $removal"
  python collect_data_results.py \
    --verbose \
    --n-times 324 \
    --result-dir ./results/focused_results_${removal} \
    --output-file results/data_runs_focused_${removal}.hdf
done
```