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
    '--output-file',
    required=True,
    help='output file'
)

args = parser.parse_args()

init_logging(args.verbose)

result_files = glob(os.path.join(args.result_dir, '*.out'))

results_dtype = numpy.dtype([
    ('template_id', int),
    ('snr_A', float),
    ('snr_E', float),
    ('snr', float),
    ('time_A', float),
    ('time_E', float)
])

results = numpy.zeros(len(result_files), dtype=results_dtype)

logging.info("Reading results files")
for i, rfname in enumerate(result_files):
    with open(rfname, 'r') as rf:
        data = rf.read().split('\n')
        #remove empty lines
        data = [d for d in data if not d == ""]
        # remove lines that start with "No"
        data = [d.split() for d in data if not d.startswith("No")]
        # there should only be one line - raise Error if there isn't
        if len(data) != 1:
            continue
            raise ValueError("Zero or more than one result line found in file")
        data = data[0]
        print(rfname)
        template_id = int(data[0].strip('[,'))
        snr_A, snr_E = float(data[1].strip('(,')), float(data[2].strip(',)'))
        snr = float(data[3].strip(','))
        time_A, time_E = float(data[6].strip('(,')), float(data[7].strip(',)'))

        results[i] = (template_id, snr_A, snr_E, snr, time_A, time_E)

logging.info("Writing results to file")
with h5py.File(args.output_file, 'w') as f:
    for k in results_dtype.names:
        print(k, results[k])
        f.create_dataset(
            k,
            data=results[k]
        )
        
logging.info("Done")