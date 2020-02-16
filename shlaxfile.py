#!/usr/bin/env shlax
from shlax.contrib.gitlab import *

PYTEST = 'py.test -svv tests'

build = Buildah(
    Copy('shlax/', 'setup.py', '/app'),
    Pip('/app'),
    commit='yourlabs/shlax',
    workdir='/app',
)

test = Script(
    Pip('.[test]'),
    Run(PYTEST),
)

buildtest = Docker(
    *test.actions,
    mount={'.': '/app'},
    workdir='/app',
)

pypi = Run(
    'pypi-release',
    stage='deploy',
    image='yourlabs/python',
)

gitlabci = GitLabCI(
    build=dict(
        stage='build',
        image='yourlabs/shlax',
    ),
    test=dict(
        stage='test',
        image=build,
    ),
    pypi=dict(
        stage='deploy',
        only=['tags'],
        image='yourlabs/python',
    ),
)
