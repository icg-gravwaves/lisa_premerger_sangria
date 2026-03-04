from pycbc.types import load_frequencyseries
import h5py

signals = range(15)
cutoff_days = [0.5, 1, 4, 7, 14]

hc_all = {}
for sig_num in signals:
    print(f'Signal {sig_num}')

    # save the characteristic strain psd
    h_c_fs = load_frequencyseries(
        f'characteristic_strain/characteristic_strain_{sig_num}_full.txt',
    )
    h_c = h_c_fs.data
    freqs = h_c_fs.sample_frequencies

    hc_all[sig_num] = {
        0: h_c
    }

    for i, days in enumerate(cutoff_days):
        print(f'{days} days before merger')

        hc_all[sig_num][days] = load_frequencyseries(
            f'characteristic_strain/characteristic_strain_{sig_num}_{days}.txt',
        )

with h5py.File('characteristic_strain/collected_characteristic_strain.hdf', 'w') as f:
    f.create_dataset(
        'frequencies',
        data=hc_all[0][0.5].sample_frequencies
    )
    f.attrs['delta_f'] = h_c_fs.delta_f
    for signal_number in signals:
        grp = f.create_group(str(signal_number))
        for days in [0] + cutoff_days:
            grp.create_dataset(
                str(days).replace('.','p'),
                data=hc_all[signal_number][days].data
            )