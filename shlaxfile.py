#!/usr/bin/env shlax
from shlax.contrib.gitlab import *

PYTEST = 'py.test -svv tests'

build = Buildah('alpine',
    Copy('shlax/', 'setup.py', '/app'),
    Pip('/app'),
    commit='yourlabs/shlax',
)

gitlabci = GitLabCIConfig(
    build=dict(
        stage='test',
        image='yourlabs/shlax',
        script='pip install -U .[test] && ' + PYTEST,
    ),
    test=dict(
        stage='test',
        image='yourlabs/python',
        script='pip install -U .[test] && ' + PYTEST,
    ),
    pypi=dict(
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
