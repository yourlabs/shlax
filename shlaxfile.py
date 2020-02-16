#!/usr/bin/env shlax
from shlax.contrib.gitlab import *

PYTEST = 'py.test -svv tests'

test = Script(
    Pip('.[test]'),
    Run(PYTEST),
)

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
        echo python3.8 -m pip > /usr/bin/pip
        chmod +x /usr/bin/pip
        '''),
        Copy('shlax/', 'setup.py', '/app'),
    ),
    Pip('/app[full]'),
    commit='docker.io/yourlabs/shlax',
    workdir='/app',
)

shlax = Container(
    build=build,
    test=Script(Run('./shlaxfile.py -d test')),
)

gitlabci = GitLabCI(
    build=dict(
        stage='build',
        image='yourlabs/shlax',
        script='CACHE_DIR=$(pwd)/.cache ./shlaxfile.py -d shlax build push',
        cache=dict(paths=['.cache'], key='cache'),
    ),
    test=dict(
        stage='test',
        script='./shlaxfile.py -d test',
        image=build,
    ),
    pypi=dict(
        stage='deploy',
        only=['tags'],
        image='yourlabs/python',
        script='pypi-release',
    ),
)
