repo_dir=/Users/gareth/lisa/lisa_premerger_sangria

python calculate_fitting_factor.py \
  --verbose \
  --days-before-merger 1 \
  --psd-files \
    A:$repo_dir/estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt \
    E:$repo_dir/estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt \
  --f-lower 1e-6 \
  --bank-file \
    $repo_dir/search/template_bank/lisa_ew_1_day_optimistic.hdf \
  --data-file \
    $repo_dir/datasets/LDC2_sangria_hm_training.hdf \
  --reduce-bank-factor \
    50
