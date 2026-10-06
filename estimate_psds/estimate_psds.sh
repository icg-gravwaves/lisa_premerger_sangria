#!/bin/bash

set -e


python estimate_psds.py \
    --input-data ../datasets/LDC2_sangria_hm_training.hdf \
    --output-dir . \
    --segment-duration 1576800 