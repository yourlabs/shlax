import pytest

from unittest.mock import patch

from shlax import *
from shlax import proc


test_args_params = [
    (
        Localhost(Run('echo hi')),
        [('sh', '-euc', 'echo hi')]
    ),
    (
        Localhost(Run('echo hi', user='jimi')),
        [('sudo', '-u', 'jimi', 'sh', '-euc', 'echo hi')]
    ),
    (
        Localhost(Run('echo hi', user='root')),
        [('sudo', 'sh', '-euc', 'echo hi')]
    ),
    (
        Ssh('host', Run('echo hi', user='root')),
        [('ssh', 'host', 'sudo', 'sh', '-euc', 'echo hi')]
    ),
    (
        Buildah('alpine', Run('echo hi')),
        [
            ('buildah', 'from', 'alpine'),
            ('buildah', 'mount', ''),
            ('buildah', 'run', '', '--', 'sh', '-euc', 'echo hi'),
            ('buildah', 'rm', ''),
        ]
    ),
    (
        Buildah('alpine', Run('echo hi', user='root')),
        [
            ('buildah', 'from', 'alpine'),
            ('buildah', 'mount', ''),
            ('buildah', 'run', '--user', 'root', '', '--', 'sh', '-euc', 'echo hi'),
            ('buildah', 'rm', ''),
        ]
    ),
    (
        Ssh('host', Buildah('alpine', Run('echo hi', user='root'))),
        [
            ('ssh', 'host', 'buildah', 'from', 'alpine'),
            ('ssh', 'host', 'buildah', 'mount', ''),
            ('ssh', 'host', 'buildah', 'run', '--user', 'root', '', '--', 'sh', '-euc', 'echo hi'),
            ('ssh', 'host', 'buildah', 'rm', ''),
        ]
    ),
]
@pytest.mark.parametrize(
    'script,commands',
    test_args_params
)
@pytest.mark.asyncio
async def test_args(script, commands):
    with Proc.mock():
        await script()
        assert commands == Proc.test
