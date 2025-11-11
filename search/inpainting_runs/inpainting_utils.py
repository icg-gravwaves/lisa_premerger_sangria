"""
This is a module to convert the current FIR filter functions to use inpainting,
but with the same interface and outputs.
"""
from scipy import signal
from functools import cache

import numpy as np
import pycbc.psd
import pycbc.types
import pycbc.fft
import pycbc.waveform
import pycbc.filter
from pycbc.strain.gate import gate_and_paint

def generate_lisa_pre_merger_psds_inpaint(
    psd_file,
    duration,
    sample_rate,
):
    """
    Load PSDs from a text file for use with inpainting methods.
    
    Parameters
    ----------
    psd_file : str
        Path to PSD file
    duration : float
        Duration of data in seconds
    sample_rate : float
        Sample rate in Hz
        
    Returns
    -------
    dict
        Dictionary with 'FD' key containing the frequency-domain PSD
    """
    flen = int(duration * sample_rate) // 2 + 1
    delta_f = 1 / duration
    delta_t = 1 / sample_rate
    td_psd_length = int(duration * sample_rate)

    psd = pycbc.psd.from_txt(
        psd_file, flen, delta_f, delta_f, is_asd_file=False
    )

    return {
        "FD": psd,
    }

def generate_data_lisa_pre_merger_inpaint(
    waveform_params,
    psds_for_datagen,
    zeroed_length,
    sample_rate,
    seed=137,
    zero_noise=False,
    no_signal=False,
):
    """
    Generate simulated LISA data with signal and noise using inpainting approach.
    
    The data is extended with zeros at the end to support variable search times.
    This differs from the FIR filter method which fixes the time-before-merger.
    
    Parameters
    ----------
    waveform_params : dict
        Waveform parameters including 'additional_end_data' for time shift
    psds_for_datagen : dict
        Dictionary of PSDs for each channel to generate noise
    zeroed_length : int
        Total length of output data (original + padding with zeros)
    sample_rate : float
        Sample rate in Hz
    seed : int, optional
        Random seed for noise generation (default: 137)
    zero_noise : bool, optional
        If True, set noise to zero (default: False)
    no_signal : bool, optional
        If True, don't add signal to data (default: False)
        
    Returns
    -------
    dict
        Dictionary of time series data for LISA_A and LISA_E channels
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

    # Extend the data to zeroed_length by adding zeroes at the end
    strain_w_A.resize(zeroed_length)
    strain_w_E.resize(zeroed_length)
    
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
):
    """
    Generate LISA waveforms in frequency domain for matched filtering.
    
    Parameters
    ----------
    waveform_params : dict
        Waveform parameters for generation
    psds_for_whitening : dict
        Dictionary of PSDs (not used in this function but kept for API consistency)
    sample_rate : float, optional
        Sample rate in Hz (default: 0.2)
        
    Returns
    -------
    dict
        Dictionary of frequency-domain waveforms for LISA_A and LISA_E channels
    """
    outs = pycbc.waveform.get_fd_det_waveform(
        ifos=['LISA_A','LISA_E'], **waveform_params
    )

    return outs



def apply_inpainting(data, psd, start_idx, end_idx):
    """
    Apply inpainting to data between start_idx and end_idx using the given PSD.
    
    Parameters
    ----------
    data : pycbc.types.TimeSeries
        Time series data to inpaint
    psd : pycbc.types.FrequencySeries
        Power spectral density
    start_idx : int
        Start index for inpainting region
    end_idx : int
        End index for inpainting region
        
    Returns
    -------
    pycbc.types.TimeSeries
        Inpainted time series data
    """
    invpsd = 1. / psd
    # Set the DC component (frequency = 0) of the inverse PSD to zero.
    # This prevents division by zero (or very small values) when computing 1/psd[0],
    # which would otherwise result in infinite or extremely large values at DC.
    invpsd[0] = 0.0
    # Use copy=True to avoid in-place modification of the input data.
    # This ensures that the original data is preserved and prevents unintended side effects.
    return gate_and_paint(data, start_idx, end_idx, invpsd, copy=True)


def pre_process_data_lisa_pre_merger_inpaint(
    data_timeseries,
    sample_rate,
    psds_for_whitening,
    inpaint_start,
    inpaint_end,
    gaps=None,
):
    """
    Truncate, inpaint and then over-whiten the data.
    
    Parameters
    ----------
    data_timeseries : dict
        Dictionary of time series data for each channel
    sample_rate : float
        Sample rate of the data
    psds_for_whitening : dict
        Dictionary of PSDs for each channel
    inpaint_start : int
        Start index for main inpainting region
    inpaint_end : int
        End index for main inpainting region
    gaps : list of tuples, optional
        List of (start_time, end_time) tuples specifying additional gaps to inpaint in seconds.
        For example: [(gap1_start_time, gap1_end_time), (gap2_start_time, gap2_end_time), ...]
        Times are converted to indices using the sample rate.
        
    Returns
    -------
    dict
        Dictionary of whitened frequency series data for each channel
    """

    # Number of samples to zero
    data_length = len(data_timeseries['LISA_A'])
    
    # Initialize painted data with the main inpainting region
    data_painted = {
        'LISA_A': apply_inpainting(
            data_timeseries['LISA_A'],
            psds_for_whitening['LISA_A'],
            inpaint_start,
            inpaint_end
        ),
        'LISA_E': apply_inpainting(
            data_timeseries['LISA_E'],
            psds_for_whitening['LISA_E'],
            inpaint_start,
            inpaint_end
        ),
    }
    
    # If additional gaps are specified, apply inpainting to each gap
    if gaps is not None:
        for gap_start_time, gap_end_time in gaps:
            # Convert times to indices
            gap_start_idx = int(gap_start_time * sample_rate)
            gap_end_idx = int(gap_end_time * sample_rate)
            
            data_painted['LISA_A'] = apply_inpainting(
                data_painted['LISA_A'],
                psds_for_whitening['LISA_A'],
                gap_start_idx,
                gap_end_idx
            )
            data_painted['LISA_E'] = apply_inpainting(
                data_painted['LISA_E'],
                psds_for_whitening['LISA_E'],
                gap_start_idx,
                gap_end_idx
            )

    inv_psd = {channel: 1. / psd for channel, psd in psds_for_whitening.items()}
    for channel in inv_psd:
        inv_psd[channel][0] = 0.0

    # Overwhiten the data
    data_ow = {
        channel: data_paint.to_frequencyseries() * inv_psd[channel]
        for channel, data_paint in data_painted.items()
    }

    return data_ow


def compute_hh_inner_product(
    waveform_params,
    psds_for_whitening,
    sample_rate,
    data_length,
    inpaint_start,
    gaps=None,
):
    """
    Compute the (h|h)(t) inner product for a waveform.
    
    This function generates a waveform, creates a mask to handle the inpainting
    region and gaps, whitens the waveform, and computes the time-dependent
    self-inner product (h|h)(t).
    
    Parameters
    ----------
    waveform_params : dict
        Parameters for waveform generation
    psds_for_whitening : dict
        Dictionary of PSDs for each channel
    sample_rate : float
        Sample rate of the data in Hz
    data_length : int
        Total length of the data in samples (including any zero padding)
    inpaint_start : int
        Index where inpainting starts (points after this are zeroed in mask)
    gaps : list of tuples, optional
        List of (start_time, end_time) tuples specifying gaps to zero in the mask in seconds.
        For example: [(gap1_start_time, gap1_end_time), (gap2_start_time, gap2_end_time), ...]
        Times are converted to indices using the sample rate.
        
    Returns
    -------
    dict
        Dictionary containing the (h|h)(t) time series for each channel
    """
    # Generate waveforms
    waveforms = generate_waveform_lisa_pre_merger_inpaint(
        waveform_params,
        psds_for_whitening,
        sample_rate=sample_rate,
    )
    
    delta_t = 1.0 / sample_rate
    inner_products = {}
    
    # Compute (h|h)(t) for each channel
    for channel in waveforms:
        # Get the waveform time series
        waveform_ts = waveforms[channel].to_timeseries()
        
        # Create a mask with ones
        mask = pycbc.types.TimeSeries(
            np.ones(data_length, dtype=waveform_ts.dtype),
            delta_t=delta_t,
            epoch=waveform_ts._epoch
        )
        
        # Zero out points after inpaint_start
        mask[inpaint_start:] = 0
        
        # Add gaps to the mask by zeroing them out
        if gaps is not None:
            for gap_start_time, gap_end_time in gaps:
                # Convert times to indices
                gap_start_idx = int(gap_start_time * sample_rate)
                gap_end_idx = int(gap_end_time * sample_rate)
                mask[gap_start_idx:gap_end_idx] = 0
        
        # Compute inverse PSD and handle DC component
        invpsd = 1.0 / psds_for_whitening[channel]
        invpsd[0] = 0.0
        
        # Convert mask to frequency series
        maskfs = mask.to_frequencyseries()
        
        # Whiten the waveform (using sqrt of inverse PSD)
        waveform = (waveforms[channel].to_frequencyseries() * invpsd**0.5).to_timeseries()
        
        # Square the whitened waveform in time domain
        waveform_sq = waveform * waveform
        
        # Multiply mask by conjugate of squared waveform in frequency domain
        masked_waveform_sq_fs = maskfs * waveform_sq.to_frequencyseries().conj()
        
        # Convert back to time series - this holds (h|h)(t)
        inner_products[channel] = masked_waveform_sq_fs.to_timeseries()
    
    return inner_products
