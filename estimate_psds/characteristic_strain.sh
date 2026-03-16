set -e

mkdir -p characteristic_strain

for signal in {0..14} ; do
  echo "Signal $signal"
  python characteristic_strain.py \
   --signal-number $signal
done

echo "Collecting results into a single file"
# Convert the characteristic strain txt files into a hdf file for ease of use
python collect_characteristic_strain.py