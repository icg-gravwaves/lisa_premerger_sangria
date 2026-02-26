for signal in {8..14} ; do
  python characteristic_strain.py \
   --signal-number $signal
done