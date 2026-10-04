#!/usr/bin/env bash
set -e
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
pip install "setuptools<58" wheel
pip install --no-build-isolation semopy==2.3.11
pip install -r requirements.txt
python3 Paper2_Python_Analysis.py
