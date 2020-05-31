#!/usr/bin/env python
"""
Shlaxfile for shlax itself.
"""

from shlax.shortcuts import *

shlax = Container(
    build=Buildah(
        Packages('python38', 'buildah', 'unzip', 'findutils', upgrade=False),
        Copy('setup.py', 'shlax', '/app'),
        Pip('/app'),
        base='quay.io/podman/stable',
        commit='shlax',
    ),
)


if __name__ == '__main__':
    print(Group(doc=__doc__).load(shlax).entry_point())
