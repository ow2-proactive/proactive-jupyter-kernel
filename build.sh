#!/usr/bin/env bash
# https://github.com/pypa/warehouse/issues/5890#issuecomment-494868157
pip install -U pip
pip install -U twine wheel setuptools

rm -rf dist/
rm -rf build/
rm -rf proactive_jupyter_kernel.egg-info/
#rm MANIFEST
python setup.py sdist --formats=zip
python setup.py bdist_wheel

twine check dist/*
