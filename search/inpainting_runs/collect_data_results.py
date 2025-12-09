import numpy
import h5py

from pycbc import init_logging, add_common_pycbc_options
import logging

import argparse
import os
from glob import glob

parser = argparse.ArgumentParser(description='Collect data results')
add_common_pycbc_options(parser)
parser.add_argument(
    '--result-dir',
    required=True,
    help='data directory'
)
parser.add_argument(
    '--time-before',
    nargs='+',
    type=float,
    help="Time-before-merger to be considered, days"
)
parser.add_argument(
    '--output-file',
    required=True,
    help='output file'
)

parser.add_argument(
    '--require-string',
    help="A string to require in the filenames we collect from"
)

parser.add_argument(
    '--exclude-string',
    help="A string to exclude from the filenames we collect from"
)

args = parser.parse_args()

init_logging(args.verbose)

result_files = sorted(glob(os.path.join(args.result_dir, '*.out')))
if args.require_string is not None:
    result_files = [f for f in result_files if args.require_string in f]

if args.exclude_string is not None:
    result_files = [f for f in result_files if args.exclude_string not in f]

results_dtype = numpy.dtype([
    ('template_id', int),
    ('snr_A', float),
    ('snr_E', float),
    ('snr', float),
    ('time_A', float),
    ('time_E', float)
])

results = {
    time_before: numpy.zeros(len(result_files), dtype=results_dtype)
    for time_before in args.time_before
}

logging.info("Reading results files")
for i, rfname in enumerate(result_files):
    with open(rfname, 'r') as rf:
        data = rf.read().split('\n')
        #remove empty lines
        data = [d for d in data if not d == ""]
        # remove lines that start with "No" or "Could"
        data = [
            d.split()
            for d in data
            if not d.startswith("No") and not d.startswith("Could")
        ]
        for dline in data:
            time_before = float(dline[0])
            try:
                time_idx = args.time_before.index(time_before)
            except ValueError:
                # Not in the list of time to be considered in this collection
                continue

            template_id = int(dline[1].strip('[,'))
            snr_A, snr_E = float(dline[2].strip('(,')), float(dline[3].strip('),'))
            snr = float(dline[4].strip(','))
            time_A, time_E = float(dline[5].strip('(,')), float(dline[6].strip(',)'))

            results[time_before][i] = (template_id, snr_A, snr_E, snr, time_A, time_E)

logging.info("Writing results to file")
with h5py.File(args.output_file, 'w') as f:
    for i, t in enumerate(args.time_before):
        t_grp = f.create_group(f'time_{t}')

        for k in results_dtype.names:
            # print(k, results[k])
            t_grp.create_dataset(
                k,
                data=results[t][k]
            )
        
logging.info("Done")
