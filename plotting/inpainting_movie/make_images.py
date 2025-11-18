import pycbc
import copy
import json
import numpy as np
import pycbc.types
from pycbc.types import MultiDetOptionAction
import pycbc.psd
import pycbc.filter
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator, FormatStrFormatter

plt.style.use('../../paper.mplstyle')

# We need to have https://github.com/icg-gravwaves/lisa_premerger_paper/
# checked out
premerger_paper_location = '/Users/iwharry/Work/LISA/lisa_premerger_paper'


psdname = 'optimistic'
signumber = '0'
data_length = 2592000
zeroed_length = 2**20
sample_rate = 0.2
flen = int(zeroed_length) // 2 + 1
delta_f = 1 / (2**20 * 5)
delta_t = 1 / sample_rate

data = pycbc.types.timeseries.load_timeseries(
        f'{premerger_paper_location}/Data/data_files/data_{psdname}_psd/signal_{signumber}.hdf',
        group=f"/LISA_A",
)
data._delta_t = 5  # Apparently it is not exactly this in the file, causing issues.
data_orig = data.copy()
data.resize(zeroed_length)

data_nonoise = pycbc.types.timeseries.load_timeseries(
        f'{premerger_paper_location}/Data/data_files/data_{psdname}_psd/signal_zero_noise_{signumber}.hdf',
        group=f"/LISA_A",
)
data_nonoise._delta_t = 5
data_nonoise.resize(zeroed_length)

psd = pycbc.psd.from_txt(
    f'{premerger_paper_location}/PSD_Files/model_AE_TDI1_SMOOTH_optimistic.txt.gz',
    flen, delta_f, delta_f, is_asd_file=False
)

invpsd = 1. / psd  # Used for inpainting
invpsd[0] = 0  # Cannot have a DC component


def inpaint_data(data, invpsd, start_idx, end_idx, copy=True):
    data = data.copy() if copy else data
    from pycbc.strain.gate import gate_and_paint
    return gate_and_paint(data, start_idx, end_idx, invpsd, copy=False)


samplerate=10
for idx, i in enumerate([x / samplerate for x in range(25*samplerate, 0, -1)]):
    print("Running for", i, "days before merger")
    merger_time = 1931852406.9997194  # This is dependent on signum, should automate getting this value!
    gate1_centre = merger_time - 86400 * 10
    gate2_centre = merger_time - 86400 * 20

    data_start = data.start_time
    data_end = data.end_time
    # Inpaint the end of the data
    lindex = data_length // 5 - int(86400 * i) // 5
    mindex = lindex + int(86400 * 7) // 5
    rindex = data_length // 5
    data_inpaintend = data.copy()
    data_inpaintend[mindex:] = 0
    data_inpaintend = inpaint_data(data_inpaintend, invpsd, lindex, mindex)
    data_inpaintendandgaps = data_inpaintend.copy()

    # Add the gaps
    if i < 10.5:
        lindex = int(float(gate1_centre - data.start_time) // 5) - 86400 // (5 * 2)
        rindex = int(float(gate1_centre - data.start_time) // 5) + 86400 // (5 * 2)
        data_inpaintendandgaps = inpaint_data(data_inpaintendandgaps, invpsd, lindex, rindex)

    if i < 20.5:
        lindex = int(float(gate2_centre - data.start_time) // 5) - 86400 // (5 * 2)
        rindex = int(float(gate2_centre - data.start_time) // 5) + 86400 // (5 * 2)
        data_inpaintendandgaps = inpaint_data(data_inpaintendandgaps, invpsd, lindex, rindex)

    # Need to record when the data is zeroed out - Times are copied from before. Make sure this is consistent!

    mask_end = np.ones(len(data_nonoise), dtype=float)
    mask_endandgaps = np.ones(len(data_nonoise), dtype=float)
    lindex = data_length // 5 - int(86400 * i) // 5
    rindex = data_length // 5
    mask_end[lindex:] = 0
    mask_endandgaps[lindex:] = 0
    lindex = int(float(gate1_centre - data.start_time) // 5) - 86400 // (5 * 2)
    rindex = int(float(gate1_centre - data.start_time) // 5) + 86400 // (5 * 2)
    mask_endandgaps[lindex:rindex] = 0
    lindex = int(float(gate2_centre - data.start_time) // 5) - 86400 // (5 * 2)
    rindex = int(float(gate2_centre - data.start_time) // 5) + 86400 // (5 * 2)
    mask_endandgaps[lindex:rindex] = 0

    # NOTE: We are using the *full* waveform here! We might want to cut at say 1 day (or 1 hour, or ...) pre-merger.
    data_to_use = data_nonoise.copy()
    wform_shift = abs(data_to_use.data).argmax()
    data_to_use.roll(-wform_shift)
    maskts_end = pycbc.types.TimeSeries(mask_end, delta_t=data_to_use.delta_t, epoch=data_to_use._epoch,
                                        dtype=data_to_use.dtype)
    maskts_endandgaps = pycbc.types.TimeSeries(mask_endandgaps, delta_t=data_to_use.delta_t, epoch=data_to_use._epoch,
                                               dtype=data_to_use.dtype)
    maskfs_end = maskts_end.to_frequencyseries()
    maskfs_endandgaps = maskts_endandgaps.to_frequencyseries()
    datasq = (data_to_use.to_frequencyseries() * invpsd ** 0.5).to_timeseries()
    datasq = datasq * datasq
    masked_datafs_end = datasq.to_frequencyseries().conj() * maskfs_end
    masked_datafts_end = masked_datafs_end.to_timeseries()
    masked_datafs_endandgaps = datasq.to_frequencyseries().conj() * maskfs_endandgaps
    masked_datafts_endandgaps = masked_datafs_endandgaps.to_timeseries()

    snr6 = pycbc.filter.matched_filter(data_to_use, data_inpaintendandgaps, psd, sigmasq=1)
    snr6_norm = snr6 / masked_datafts_endandgaps ** 0.5 / 2 ** 0.5
    snr6_norm_sq = abs(snr6_norm) ** 2
    invalid_sample = (30 + 28 - i) * 86400 // 5
    snr6_norm[int(invalid_sample):] = 0
    print("invalid sample index:", invalid_sample)

    # Convert sample times to "days relative to merger" for the x-axis:
    sample_times = np.asarray(snr6_norm.sample_times)  # epoch seconds
    sample_times_rel_days = (sample_times - merger_time) / 86400.0  # days (time - merger_time)

    # Compute the "current time" relative to merger and textual label (X days before merger)
    current_time = float(sample_times[0]) + (30.0 - float(i)) * 86400.0
    current_time_rel_days = (current_time - merger_time) / 86400.0
    days_before_merger = (merger_time - current_time) / 86400.0  # positive if before merger
    if days_before_merger >= 0:
        current_label = f'{days_before_merger:.1f} days before merger'
    else:
        current_label = f'{abs(days_before_merger):.1f} days after merger'

    # Prepare the figure
    fig, ax = plt.subplots()

    # Plot SNR vs days relative to merger
    ax.plot(sample_times_rel_days, snr6_norm, color='tab:blue', label='_nolegend_')

    # Vertical line at current time (in days relative to merger)
    ax.axvline(current_time_rel_days, color='tab:orange', linestyle='--', label='Current time')

    # Gaps: compute in days relative to merger and show as semi-transparent gray patches if current time has reached the gap start
    gap_halfwidth_days = 0.5  # 0.5 day each side -> 1 day wide
    gate1_start_rel = (gate1_centre - gap_halfwidth_days * 86400.0 - merger_time) / 86400.0
    gate1_end_rel = (gate1_centre + gap_halfwidth_days * 86400.0 - merger_time) / 86400.0
    gate2_start_rel = (gate2_centre - gap_halfwidth_days * 86400.0 - merger_time) / 86400.0
    gate2_end_rel = (gate2_centre + gap_halfwidth_days * 86400.0 - merger_time) / 86400.0

    ymax = max(10, np.nanmax(np.abs(snr6_norm)) * 1.1)  # dynamic y limit but at least 10
    ymax = 10
    ymin = -ymax
    ax.set_ylim(-ymax, ymax)

    if current_time_rel_days >= gate1_start_rel:
        ax.axvspan(gate1_start_rel, gate1_end_rel, color='grey', alpha=0.28, label='_nolegend_')
        ax.text((gate1_start_rel + gate1_end_rel) / 2, ymax * 0.8, 'Gap', ha='center', va='center',
                color='black', alpha=0.9)

    if current_time_rel_days >= gate2_start_rel:
        ax.axvspan(gate2_start_rel, gate2_end_rel, color='grey', alpha=0.28, label='_nolegend_')
        ax.text((gate2_start_rel + gate2_end_rel) / 2, ymax * 0.8, 'Gap', ha='center', va='center',
                color='black', alpha=0.9)

    # Labels and ticks: x axis in days relative to merger
    ax.set_xlabel('Time - merger time (days)')
    ax.set_ylabel('SNR')

    # Make x ticks reasonable and formatted to 1 decimal place
    ax.xaxis.set_major_locator(MaxNLocator(nbins=8))
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    ax.tick_params(axis='both', which='major')

    # Minor grid lines for readability
    ax.grid(True, which='major', linestyle='--', alpha=0.4)
    ax.grid(True, which='minor', linestyle=':', alpha=0.15)
    ax.minorticks_on()

    # Put the days-before-merger label next to the orange line, vertically oriented for compactness
    # Use a small offset in days so the text doesn't cover the line
    x_offset_days = max(0.02, (sample_times_rel_days.max() - sample_times_rel_days.min()) * 0.01)
    #ax.text(current_time_rel_days + x_offset_days, ymax * 0.92, current_label, rotation=90,
    #        va='top', ha='left', fontsize=9, color='tab:orange',
    #        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))

    # Legend
    ax.legend(loc='upper right')

    # Title with a short descriptor
    #ax.set_title('Matched-filter SNR (inpaint end & gaps)', fontsize=12)

    plt.tight_layout()
    plt.savefig(f'snr_inpaintendandgaps_{idx}.png', dpi=600)
    if int(i*20) // 20 in [14, 7, 4, 1]:
        plt.savefig(f'../paper/images/snr_{i}_days_before_merger.pdf')

    plt.close(fig)
