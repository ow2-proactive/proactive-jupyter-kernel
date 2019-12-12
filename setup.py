#!/usr/bin/env python
# setup.py generated by flit for tools that don't yet use PEP 517

# from distutils.core import setup
from setuptools import setup
import datetime

packages = \
    ['proactive-jupyter-kernel']

package_data = \
    {'': ['*']}

install_requires = \
    ['pexpect>=4.0', 'proactive', 'jupyter_client', 'IPython', 'traitlets', 'ipykernel', 'notebook', 'configparser',
     'matplotlib', 'networkx', 'pygraphviz', 'tornado==5.1.1']

now = datetime.datetime.now()

gradle_properties = {}
with open('gradle.properties') as fp:
    for line in fp:
        if '=' in line:
            name, value = line.replace('\n', '').split('=', 1)
            if "SNAPSHOT" in value:
                dev_version = "." + now.strftime("%y%m%d%H%M") + "dev"
                # dev_version = "." + now.strftime("%y%m%d%H%M")
                value = value.replace("-SNAPSHOT", dev_version)
            gradle_properties[name] = value

with open("README.md", "r") as fh:
    try:
        long_description = fh.read()
    except (OSError, IOError):
        long_description = "Not available"

setup(name='proactive-jupyter-kernel',
      version=gradle_properties["version"],
      description='A proactive kernel for Jupyter',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='ActiveEon',
      author_email='contact@activeeon.com',
      url='https://github.com/ow2-proactive/proactive-jupyter-kernel',
      packages=packages,
      package_dir={'proactive-jupyter-kernel': 'proactive-jupyter-kernel'},
      package_data=package_data,
      install_requires=install_requires,
      license="BSD 2-Clause License"
      )
