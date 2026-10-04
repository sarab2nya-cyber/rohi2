@echo off
set OMP_NUM_THREADS=1
pip install "setuptools<58" wheel
pip install --no-build-isolation semopy==2.3.11
pip install -r requirements.txt
python Paper1_Python_Analysis.py
pause
