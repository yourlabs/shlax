#!/usr/bin/env shlax
from shlax.contrib.gitlab import *

PYTEST = 'py.test -svv tests'

build = Buildah('alpine',
    Copy('shlax', 'setup.py', '/app'),
    Pip('/app'),
    commit='yourlabs/shlax',
)

gitlabci = GitLabCIConfig(
    Job('test',
        stage='test',
        image='yourlabs/python',
        script='pip install -U .[test] && ' + PYTEST,
    ),
    Job('pypi',
        stage='deploy',
        image='yourlabs/python',
        script='pypi-release',
        only=['tags']
    ),
)

test = Script(
    gitlabci,
    Run('gitlab-runner exec docker test'),
)
