for signal in {8..14} ; do
  python characteristic_strain.py \
   --signal-number $signal
done

# Convert the characteristic strain txt files into a hdf file for ease of use
python collect_characteristic_strain.py