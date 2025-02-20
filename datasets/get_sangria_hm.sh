# File location:
# https://lisa-ldc.lal.in2p3.fr/media/uploads/LDC2_sangria_hm_training.h5

if ! [ -f LDC2_sangria_hm_training.hdf ] ; then
  wget --show-progress https://lisa-ldc.lal.in2p3.fr/media/uploads/LDC2_sangria_hm_training.h5
  mv LDC2_sangria_hm_training.h5 LDC2_sangria_hm_training.hdf
fi