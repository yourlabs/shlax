#!/usr/bin/env shlax
from shlax.contrib.gitlab import *

PYTEST = 'py.test -svv tests'

build = Buildah(
    'quay.io/podman/stable',
    Packages('python38', 'buildah', 'unzip', 'findutils', 'python3-yaml', upgrade=False),
    Async(
        # python3.8 on centos with pip dance ...
        Run('''
        curl -o setuptools.zip https://files.pythonhosted.org/packages/42/3e/2464120172859e5d103e5500315fb5555b1e908c0dacc73d80d35a9480ca/setuptools-45.1.0.zip
        unzip setuptools.zip
        mkdir -p /usr/local/lib/python3.8/site-packages/
        sh -c "cd setuptools-* && python3.8 setup.py install"
        easy_install-3.8 pip
        '''),
        Copy('shlax/', 'setup.py', '/app'),
    ),
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
