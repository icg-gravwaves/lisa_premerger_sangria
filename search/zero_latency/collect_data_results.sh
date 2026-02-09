set -e

for days_before in 0.5 1 4 7 14  ; do
  sanitize_dbm=`echo "$days_before" | sed 's/\./p/g'`

  for remove in 'raw' 'remove' ; do
    for model in model estimate ; do
      echo $model $remove $sanitize_dbm
      python collect_data_results.py \
        --verbose \
        --result-dir ./results/psd_$model/$remove/${sanitize_dbm} \
        --output-file ./results/psd_$model/data_runs_${remove}_${days_before}_results.hdf
    done
  done
done

