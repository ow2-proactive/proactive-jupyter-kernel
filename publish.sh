#!/usr/bin/env bash
command -v source >/dev/null 2>&1 || {
  echo "I require source but it's not installed.  Aborting." >&2; exit 1;
}

pip install virtualenv

virtualenv -p python3 env
source env/bin/activate

pip install -U twine

#twine upload dist/* --config-file .pypirc

if [[ $JENKINS_JNLP_URL ]]
then
   twine upload -r pypi dist/* --config-file /home/activeeon/.pypirc
else
   twine upload -r pypi dist/*
fi
