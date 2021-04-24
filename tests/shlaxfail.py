#!/usr/bin/env python
"""
Shlaxfile for shlax itself.
"""

from shlax.shortcuts import *

shlax = Container(
    build=Buildah(
        Packages('prout', upgrade=False),
        base='alpine',
        commit='shlaxfail',
    ),
)


if __name__ == '__main__':
    print(Group(doc=__doc__).load(shlax).entry_point())
