#!/bin/bash
command -v source >/dev/null 2>&1 || {
  echo "I require source but it's not installed.  Aborting." >&2; exit 1;
}

pip install virtualenv

virtualenv -p python3 env
source env/bin/activate

pip install -U pip twine wheel setuptools

rm -rf dist/
rm -rf build/
rm -rf proactive_jupyter_kernel.egg-info/
#rm MANIFEST
python setup.py sdist --formats=zip
python setup.py bdist_wheel

twine check dist/*
