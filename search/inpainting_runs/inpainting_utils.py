"""
This is a module to convert the current FIR filter functions to use inpainting,
but with the same 
"""
from scipy import signal

import pycbc.psd
import pycbc.types
import pycbc.fft
import pycbc.waveform
from pycbc.strain.gate import gate_and_paint

def generate_lisa_pre_merger_psds_inpaint(
    psd_file,
    duration,
    sample_rate,
    kernel_length=17280,
):
    """
    This is actually pretty much just loading the PSDs
    """
    flen = int(duration * sample_rate) // 2 + 1
    delta_f = 1 / duration
    delta_t = 1 / sample_rate
    td_psd_length = int(duration * sample_rate)

    psd = pycbc.psd.from_txt(
        psd_file, flen, delta_f, delta_f, is_asd_file=False
    )

    # Time domain pycbc PSD
    td_psd = pycbc.types.TimeSeries(
        pycbc.types.zeros(td_psd_length),
        delta_t=delta_t,
    )

    pycbc.fft.ifft(psd, td_psd)

    return {
        "TD": td_psd,
        "FD": psd,
    }

def generate_data_lisa_pre_merger_inpaint(
    waveform_params,
    psds_for_datagen,
    sample_rate,
    seed=137,
    zero_noise=False,
    no_signal=False,
    duration=None,
):
    """
    """

    # Generate injection
    outs = pycbc.waveform.get_fd_det_waveform(
        ifos=['LISA_A','LISA_E','LISA_T'],
        **waveform_params
    )

    # Shift waveform so the merger is not at the end of the data
    outs['LISA_A'] = outs['LISA_A'].cyclic_time_shift(-waveform_params['additional_end_data'])
    outs['LISA_E'] = outs['LISA_E'].cyclic_time_shift(-waveform_params['additional_end_data'])

    # FS waveform to TD
    tout_A = outs['LISA_A'].to_timeseries()
    tout_E = outs['LISA_E'].to_timeseries()

    # Generate TD noise from the original PSDs
    strain_w_A = pycbc.noise.noise_from_psd(
        len(tout_A),
        tout_A.delta_t,
        psds_for_datagen['LISA_A'],
        seed=seed,
    )
    strain_w_E = pycbc.noise.noise_from_psd(
        len(tout_E),
        tout_E.delta_t,
        psds_for_datagen['LISA_E'],
        seed=seed + 1,
    )

    # We need to make sure the noise times match the signal
    strain_w_A._epoch = tout_A._epoch
    strain_w_E._epoch = tout_E._epoch

    # If zero noise, set noise to zero
    if zero_noise:
        strain_w_A *= 0.0
        strain_w_E *= 0.0

    # Only add signal if no_signal=False
    if not no_signal:
        strain_w_A[:] += tout_A[:]
        strain_w_E[:] += tout_E[:]

    # If duration is specified, discard the extra data
    if duration is not None:
        if duration > tout_A.duration:
            raise RuntimeError(
                "Specified duration is longer than the generated waveform"
            )
        nkeep = int(duration * sample_rate)
        # New start time will be nkeep sample time
        new_epoch = strain_w_A.sample_times[-nkeep]
        strain_w_A = pycbc.types.TimeSeries(
            strain_w_A.data[-nkeep:],
            delta_t=strain_w_A.delta_t,
        )
        strain_w_E = pycbc.types.TimeSeries(
            strain_w_E.data[-nkeep:],
            delta_t=strain_w_E.delta_t,
        )
        # Set the start time so that the GPS time is still correct
        strain_w_A.start_time = new_epoch
        strain_w_E.start_time = new_epoch
    
    return {
        "LISA_A": strain_w_A,
        "LISA_E": strain_w_E,
    }


@cache
def get_window(window_length):
    if window_length:
        return signal.windows.hann(window_length * 2 + 1)[:window_length]
    else:
        return None


def generate_waveform_lisa_pre_merger_inpaint(
        waveform_params,
        psds_for_whitening,
        sample_rate=0.2,
        **kwargs
):
    outs = pycbc.waveform.get_fd_det_waveform(
        ifos=['LISA_A','LISA_E'], **waveform_params
    )

    return outs



def apply_inpainting(data, psd, start_idx, end_idx):
    invpsd = 1. / psd
    return gate_and_paint(data, start_idx, end_idx, invpsd, copy=False)


def pre_process_data_lisa_pre_merger_inpaint(
    data_timeseries,
    sample_rate,
    psds_for_whitening,
    window_length=None,
    cutoff_time=None,
    **kwargs
):
    """
    Truncate, inpaint and then over-whiten the data
    """
    window = get_window(window_length)

    # Number of samples to zero
    nctf = int(cutoff_time * sample_rate)
    data_length = len(data_timeseries['LISA_A'])
    # index of the start of the gate
    lindex = int(data_length - nctf)
    # index at the end of the data
    rindex = int(data_length)
    data_painted = {
        'LISA_A': apply_inpainting(
            data_timeseries['LISA_A'],
            psds_for_whitening['LISA_A'],
            lindex,
            rindex
        ),
        'LISA_E': apply_inpainting(
            data_timeseries['LISA_E'],
            psds_for_whitening['LISA_E'],
            lindex,
            rindex
        ),
    }

    inv_psd = {channel: 1. / psd for channel, psd in psds_for_whitening.items()}

    # Overwhiten the data
    data_ow = {
        channel: data_paint.to_frequencyseries() * inv_psd[channel] ** 2
        for channel, data_paint in data_painted.items()
    }

    strain_ow = {
        channel: data_f.to_timeseries()
        for channel, data_f in data_ow.items()
    }

    return strain_ow
