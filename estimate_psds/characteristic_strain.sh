set -e

mkdir -p characteristic_strain

# start from a fresh file so re-runs don't collide with stale signal groups
rm -f characteristic_strain/collected_characteristic_strain.hdf

for signal in {0..14} ; do
  echo "Signal $signal"
  python characteristic_strain.py \
   --signal-number $signal
done
