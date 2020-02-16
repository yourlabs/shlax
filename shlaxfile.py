#!/usr/bin/env shlax
"""
Shlaxfile for shlax itself.
"""

from shlax.shortcuts import *

build = Buildah(
    Run('echo hi'),
    Packages('python38'),
    base='quay.io/podman/stable',
)
