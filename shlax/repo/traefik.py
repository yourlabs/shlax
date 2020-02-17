#!/usr/bin/env shlax
"""
Manage a traefik container maintained by Shlax community.
"""

from shlax import *

main = Docker(
    name='traefik',
    image='traefik:v2.0.0',
    networks=['web'],
    command=[
        '--entrypoints.web.address=:80',
        '--providers.docker',
        '--api',
    ],
    ports=[
        '80:80',
        '443:443',
    ],
    volumes=[
        '/var/run/docker.sock:/var/run/docker.sock:ro',
        '/etc/traefik/acme/:/etc/traefik/acme/',
        '/etc/traefik/htpasswd:/htpasswd:ro',
    ],
    labels=[
        'traefik.http.routers.traefik.rule=Host(`{{ url.split("/")[2] }}`)',
        'traefik.http.routers.traefik.service=api@internal',
        'traefik.http.routers.traefik.entrypoints=web',
    ],
    doc='Current traefik instance',
)

install = Script(
    Htpasswd('./htpasswd', 'root'),
    main.bind('up'),
    doc='Deploy a Traefik instance',
)

up = main.bind('up')
rm = main.bind('rm')
