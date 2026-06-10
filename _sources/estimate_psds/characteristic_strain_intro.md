# Characteristic Strain

To calculate the expected SNR as the signal evolves toward merger, we use the characteristic strain. This is explained more in the paper, but basically this is a transform of the $h_+$ signal strain and the strain noise data so that expected SNR can easily be seen.

We calculate the characteristic strain for each signal using `characteristic_strain.py`, and then collect them together using `collect_characteristic_strain.py`.

`characteristic_strain.py` produces characteristic strain outputs for each day-before-merger cutoff, and the full strain. The different time-before-merger simply have the characteristic strain cut off at the estimated frequency given the time-before-merger. We could have done this differently, using frequency cutoffs corresponding to the relevant time before merger in downstream analyses instead of here, but this just keeps things neatly in one place.

`collect_characteristic_strain.py` collects the text file outputs and puts them into a single hdf file for ease of use.

## Usage

```bash
for signal in {0..14} ; do
  echo "Signal $signal"
  python characteristic_strain.py \
   --signal-number $signal
done

python collect_characteristic_strain.py
```

These results are plotted with `characteristic_strain.ipynb` (the next page).

The characteristic strain result file is not given in the repo due to its size. Re-generation is relatively quick and not too computationally intensive though.