python ./sensitive_time_distance.py \
  --mass-range 1e4 5e9 \
  --log-mass-spacing \
  --n-mass-points 50 \
  --n-sky-points 20 \
  --times 0 3600 43200 86400 345600 604800 1209600 \
  --psd-files \
    A:../estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt \
    E:../estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt \
  --output-file sensitive_distance.hdf \
  --parallelize-range 0/10
