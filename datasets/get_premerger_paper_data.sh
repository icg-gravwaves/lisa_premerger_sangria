# Get stuff from the LISA premerger paper that we are going to reuse in this one

git_url=https://github.com/icg-gravwaves/lisa_premerger_paper/raw/main/

if ! [ -f model_AE_TDI1_SMOOTH_optimistic.txt.gz ] ; then
    wget --show-progress $git_url/PSD_Files/model_AE_TDI1_SMOOTH_optimistic.txt.gz
fi
if ! [ -f model_AE_TDI1_optimistic.txt.gz ] ; then
    wget --show-progress $git_url/PSD_Files/model_AE_TDI1_optimistic.txt.gz
fi
if ! [ -f model_AE_TDI1_SMOOTH_optimistic.txt ] ; then
    gzip -dk model_AE_TDI1_SMOOTH_optimistic.txt.gz
fi
if ! [ -f model_AE_TDI1_optimistic.txt ] ; then
    gzip -dk model_AE_TDI1_optimistic.txt.gz
fi
if ! [ -f model_T_TDI1_optimistic.txt.gz ] ; then
    wget --show-progress $git_url/PSD_Files/model_T_TDI1_optimistic.txt.gz
fi
if ! [ -f model_T_TDI1_optimistic.txt ] ; then
    gzip -dk model_T_TDI1_optimistic.txt.gz
fi
if ! [ -f AE_response_function.txt ] ; then
    wget --show-progress $git_url/PSD_Files/AE_response_function.txt
fi

if ! [ -f injections.json ] ; then
    wget --show-progress $git_url/Data/injections.json
fi
if ! [ -f signal_0.hdf ] ; then
    wget --show-progress $git_url/Data/data_files/data_optimistic_psd/signal_0.hdf
fi
if ! [ -f signal_zero_noise_0.hdf ] ; then
    wget --show-progress $git_url/Data/data_files/data_optimistic_psd/signal_zero_noise_0.hdf
fi
for bank_time_before in 0.5 1 4 7 14 ; do
    if ! [ -f lisa_ew_${bank_time_before}_day_optimistic.hdf ] ; then
        wget --show-progress $git_url/Search/Template_Banks/lisa_ew_${bank_time_before}_day_optimistic.hdf
    fi
done