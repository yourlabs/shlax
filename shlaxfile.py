#!/usr/bin/env shlax
"""
Shlaxfile for shlax itself.
"""

from shlax.shortcuts import *

build = Buildah(
    'quay.io/podman/stable',
    Run('echo hi'),
    commit='docker.io/yourlabs/shlax',
    workdir='/app',
)

build()
