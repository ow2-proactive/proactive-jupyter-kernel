#!/bin/bash
command -v source >/dev/null 2>&1 || {
  echo "I require source but it's not installed.  Aborting." >&2; exit 1;
}

which python3
which pip3
python -V
pip -V
python3 -V
pip3 -V

curl https://bootstrap.pypa.io/pip/3.5/get-pip.py -o get-pip.py
python3 get-pip.py
hash -r
pip3 -V

#pip3 list
# Python 2 and 3.5 are being deprecated
#pip3 install -U pip
pip3 install virtualenv
pip3 list

#which virtualenv

virtualenv -p python3 env
#virtualenv -p python2 env
source env/bin/activate

# https://github.com/pypa/warehouse/issues/5890#issuecomment-494868157
pip3 install certifi==2021.10.8
pip3 install -U twine wheel setuptools

rm -rf dist/
rm -rf build/
rm -rf proactive_jupyter_kernel.egg-info/
#rm MANIFEST
python setup.py sdist --formats=zip
python setup.py bdist_wheel

twine check dist/*
