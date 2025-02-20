shared_args="""
  --mass-range 20 5e8 \
  --log-mass-spacing \
  --verbose \
  --n-mass-points 50 \
  --n-sky-points 50 \
  --times 0 3600 43200 86400 345600 604800 1209600 \
"""

# python ./sensitive_time_distance.py \
#   $shared_args \
#   --psd-files \
#     A:../estimate_psds/A_sangria_hm_SMOOTHED_PSD.txt \
#     E:../estimate_psds/E_sangria_hm_SMOOTHED_PSD.txt \
#   --output-file sensitive_distance_smoothed.hdf 


python ./sensitive_time_distance.py \
  $shared_args \
  --psd-files \
    A:../estimate_psds/model_AE_TDI1_SMOOTH_optimistic.txt \
    E:../estimate_psds/model_AE_TDI1_SMOOTH_optimistic.txt \
  --output-file sensitive_distance_model.hdf 