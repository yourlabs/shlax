#!/usr/bin/env shlax
from shlax import *

main = Container(
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
    ]
)
