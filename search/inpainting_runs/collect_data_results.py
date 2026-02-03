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
        print(string)
        print(m)
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
for i, rfname in enumerate(result_files):
    logging.info(rfname)
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
