#!/usr/bin/env python
# setup.py generated by flit for tools that don't yet use PEP 517

from distutils.core import setup
import datetime

packages = \
    ['proactive-jupyter-kernel']

package_data = \
    {'': ['*']}

install_requires = \
    ['pexpect>=4.0', 'proactive', 'jupyter_client', 'IPython', 'traitlets', 'ipykernel', 'notebook', 'configparser',
     'matplotlib', 'networkx']

now = datetime.datetime.now()

gradle_properties = {}
with open('gradle.properties') as fp:
    for line in fp:
        if '=' in line:
            name, value = line.replace('\n', '').split('=', 1)
            if "SNAPSHOT" in value:
                #dev_version = ".dev" + str(int(time.time()))
                dev_version = "." + now.strftime("%Y.%m.%d.%H.%M")
                value = value.replace("-SNAPSHOT", dev_version)
            gradle_properties[name] = value

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='proactive-jupyter-kernel',
      version=gradle_properties["version"],
      description='A proactive kernel for Jupyter',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='ActiveEon',
      author_email='contact@activeeon.com',
      url='https://github.com/ow2-proactive/proactive-jupyter-kernel',
      packages=packages,
      package_data=package_data,
      install_requires=install_requires
      )
