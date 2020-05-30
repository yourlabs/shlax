#!/usr/bin/env python
"""
Shlaxfile for shlax itself.
"""

from shlax.shortcuts import *

shlax = Container(
    build=Buildah(
        User('app', '/app', getenv('_CONTAINERS_ROOTLESS_UID')),
        Packages('python38', 'buildah', 'unzip', 'findutils'),
        Copy('setup.py', 'shlax', '/app'),
        #Pip('/app', pip='pip3.8'),
        base='quay.io/podman/stable',
        commit='shlax',
    ),
)


if __name__ == '__main__':
    print(Group(doc=__doc__).load(shlax).entry_point())
