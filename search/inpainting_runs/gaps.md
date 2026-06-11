# Data gaps

One of the main advantages with using inpainting over the zero-latency filter is the ability to ride out gaps in the data.
We ran a special analysis on signal 0 where we added gaps into the data in the days before merger to demonstrate this ability.

## Running the analysis
We re-ran `data-runs.py` over the time period of interest, but with gaps added to the data using the `--gaps` option.

This was run using `job.sub` as the template once again, with the `gaps` option added. Data results were collected using `collect_data_results.py` as before.