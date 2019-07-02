#!/usr/bin/env bash
#twine upload dist/* --config-file .pypirc

if [[ $JENKINS_JNLP_URL ]]
then
   twine upload -r pypi dist/* --config-file /home/activeeon/.pypirc
else
   twine upload -r pypi dist/*
fi
