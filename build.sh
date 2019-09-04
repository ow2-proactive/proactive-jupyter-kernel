#!/bin/bash
command -v source >/dev/null 2>&1 || {
  echo "I require source but it's not installed.  Aborting." >&2; exit 1;
}

#pip list

pip install virtualenv
#which virtualenv

virtualenv -p python3 env
#virtualenv -p python2 env
source env/bin/activate

#pip install -U pip

# https://github.com/pypa/warehouse/issues/5890#issuecomment-494868157
pip install -U twine wheel setuptools

rm -rf dist/
rm -rf build/
rm -rf proactive_jupyter_kernel.egg-info/
#rm MANIFEST
python setup.py sdist --formats=zip
python setup.py bdist_wheel

twine check dist/*
