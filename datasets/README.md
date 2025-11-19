# Dataset Download Scripts

This directory contains bash scripts to fetch the necessary datasets for the notebooks and analyses in this repository.

## Available Scripts

### get_premerger_paper_data.sh

Downloads data files from the [lisa_premerger_paper](https://github.com/icg-gravwaves/lisa_premerger_paper) repository, including:
- PSD files (model_AE_TDI1_SMOOTH_optimistic.txt.gz, model_AE_TDI1_optimistic.txt.gz)
- Injection parameters (injections.json)
- Signal data files (signal_0.hdf, signal_zero_noise_0.hdf)
- Template banks (lisa_ew_1_day_optimistic.hdf)

**Usage:**
```bash
cd datasets
bash get_premerger_paper_data.sh
```

### get_sangria_hm.sh

Downloads the Sangria dataset with higher modes.

**Usage:**
```bash
cd datasets
bash get_sangria_hm.sh
```

## Notes

- All downloaded files are ignored by git (see .gitignore)
- Scripts check if files already exist before downloading to avoid unnecessary downloads
- Notebooks and analysis scripts reference these files using relative paths to this directory
