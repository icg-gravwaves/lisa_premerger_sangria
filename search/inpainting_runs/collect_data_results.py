import numpy
import h5py
import re

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
    '--n-times',
    type=int,
    default=300,
    help="Number of times before merger which are condidered"
)
parser.add_argument(
    '--output-file',
    required=True,
    help='output file'
)


args = parser.parse_args()

init_logging(args.verbose)

result_files = sorted(glob(os.path.join(args.result_dir, '*.out')))

results_dtype = numpy.dtype([
    ('template_id', int),
    ('snr_A', float),
    ('snr_E', float),
    ('snr', float),
    ('time_A', float),
    ('time_E', float),
    ('time_before_merger', float),
    ('data_end_time', int)
])

results = numpy.zeros(
    int(len(result_files) * args.n_times * 1.1), # Add some extra, zeros will be removed anyway
    dtype=results_dtype
)

logging.info('%d results files found', len(result_files))

PAT = re.compile(
    r'^(?:np|numpy)\.(?P<type>[A-Za-z_]\w*)\(\s*'
    r'(?P<number>[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?)'
    r'\s*\)$'
)

def numpy_string_to_number(string):
    """Convert a string to a number if the string has the format np.int64(X) or other numpy types
    using the datatype defined"""
    assert 'np' in string or 'numpy' in string
    m = PAT.match(string.strip())
    if not m:
        raise ValueError("not a numpy-constructor string")
    t = m.group('type')        # e.g. 'int64' or 'float64'
    nstr = m.group('number')   # e.g. '-3.2e+01' or '5'
    # convert according to type name
    if 'int' in t:
        # use int of float(...) to accept things like '5.0'
        return int(float(nstr))
    if 'float' in t or 'double' in t:
        return float(nstr)

def to_number(string, as_int=False):
    if 'numpy' in string or 'np' in string:
        return numpy_string_to_number(string)
    else:
        if as_int:
            return int(string)
        else:
            return float(string)

def clean_item(s):
    snew = s.strip('()[]\,')
    if '(' in snew:
        snew += ')'
    return snew
    
logging.info("Reading results files")
count_valid = 0
for i, rfname in enumerate(result_files):
    logging.debug(rfname)
    data_end_time = int(os.path.basename(rfname).split('.')[0].split('_')[-1])
    with open(rfname, 'r') as rf:
        raw_lines = rf.read().split('\n')

        for ln in raw_lines:
            parts = ln.split()
            # Check that this line starts with a number - this means it is a result
            try:
                float(parts[0])
            except (ValueError, IndexError):
                continue
            # clean parts and filter out any leftover pure-type tokens
            parts = [clean_item(p) for p in parts if not re.match(r"^<class\s+'numpy\.[^']+'>$", p)]
            if len(parts) < 7:
                # unexpected line format, skip
                continue

            time_before = to_number(parts[0])
            template_id = to_number(parts[1], as_int=True)
            snr_A = to_number(parts[2])
            snr_E = to_number(parts[3])
            snr = to_number(parts[4])
            time_A = to_number(parts[5])
            time_E = to_number(parts[6])

            results[count_valid] = (template_id, snr_A, snr_E, snr, time_A, time_E, time_before, data_end_time)
            count_valid += 1

logging.info('%d result lines found', count_valid)
logging.info("Writing results to file")
with h5py.File(args.output_file, 'w') as f:
    valid = results['snr'] > 0
    for k in results_dtype.names:
        # print(k, results[k])
        f.create_dataset(
            k,
            data=results[k][valid]
        )
    
logging.info("Done")
