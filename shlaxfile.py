#!/usr/bin/env shlax
from shlax.contrib.gitlab import *

gitlabci = GitLabCIConfig(
    Job('test',
        stage='test',
        image='yourlabs/python',
        script='pip install -U .[test] && py.test -svv tests',
    ),
    Job('pypi',
        stage='deploy',
        image='yourlabs/python',
        script='pypi-release',
        only=['tags']
    ),
)
