import pytest
from unittest.mock import Mock, call

from shlax import Proc


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'args',
    (
        ['echo hi'],
        ['sh -c "echo hi"'],
        ['sh', '-c', 'echo hi'],
    )
)
async def test_proc(args):
    proc = Proc(*args, quiet=True)
    assert not proc.waited
    assert not proc.started
    await proc.wait()
    assert proc.waited
    assert proc.started
    assert proc.out == 'hi'
    assert proc.err == ''
    assert proc.out_raw == b'hi\n'
    assert proc.err_raw == b''
    assert proc.rc == 0


@pytest.mark.asyncio
async def test_wait_unbound():
    proc = await Proc('echo hi', quiet=True).wait()
    assert proc.out == 'hi'


@pytest.mark.asyncio
async def test_rc_1():
    proc = await Proc(
        'sh', '-euc', 'NON EXISTING COMMAND',
        quiet=True,
    ).wait()
    assert proc.rc != 0
    assert proc.err == 'sh: line 1: NON: command not found'


@pytest.mark.asyncio
async def test_prefix():
    """
    Test output prefixes for when executing multiple commands in parallel.
    """
    Proc.prefix_length = 0  # reset

    stdout = Mock()
    await Proc(
        'echo hi',
        stdout=stdout,
        prefix='test_prefix',
    ).wait()
    await Proc(
        'echo hi',
        stdout=stdout,
        prefix='test_prefix_1'
    ).wait()
    await Proc(
        'echo hi',
        stdout=stdout,
        prefix='test_prefix',
    ).wait()

    assert stdout.buffer.write.mock_calls == [
        call(
            Proc.prefix_colors[0].encode()
            + b'test_prefix '
            + Proc.colors.reset.encode()
            + b'| '
            + Proc.colors.bgray.encode()
            + b'+ echo hi'
            + Proc.colors.reset.encode()
            + b'\n'
        ),
        call(
            Proc.prefix_colors[0].encode()
            + b'test_prefix '
            + Proc.colors.reset.encode()
            + b'| hi'
            + Proc.colors.reset.encode()
            + b'\n'
        ),
        call(
            Proc.prefix_colors[1].encode()
            + b'test_prefix_1 '
            + Proc.colors.reset.encode()
            + b'| '
            + Proc.colors.bgray.encode()
            + b'+ echo hi'
            + Proc.colors.reset.encode()
            + b'\n'
        ),
        call(
            Proc.prefix_colors[1].encode()
            # padding has been added because of output1
            + b'test_prefix_1 '
            + Proc.colors.reset.encode()
            + b'| hi'
            + Proc.colors.reset.encode()
            + b'\n'
        ),
        call(
            Proc.prefix_colors[0].encode()
            # padding has been added because of output1
            + b'  test_prefix '
            + Proc.colors.reset.encode()
            + b'| '
            + Proc.colors.bgray.encode()
            + b'+ echo hi'
            + Proc.colors.reset.encode()
            + b'\n'
        ),
        call(
            Proc.prefix_colors[0].encode()
            # padding has been added because of output1
            + b'  test_prefix '
            + Proc.colors.reset.encode()
            + b'| hi'
            + Proc.colors.reset.encode()
            + b'\n'
        )
    ]


@pytest.mark.asyncio
async def test_prefix_multiline():
    Proc.prefix_length = 0  # reset
    proc = await Proc(
        'echo -e "a\nb"',
        stdout=Mock(),
        prefix='test_prefix',
    ).wait()
    assert proc.stdout.buffer.write.mock_calls == [
        call(
            Proc.prefix_colors[0].encode()
            + b'test_prefix '
            + Proc.colors.reset.encode()
            + b'| '
            + Proc.colors.bgray.encode()
            + b"+ echo -e 'a\\nb'"
            + Proc.colors.reset.encode()
            + b'\n'
        ),
        call(
            Proc.prefix_colors[0].encode()
            + b'test_prefix '
            + Proc.colors.reset.encode()
            + b'| a'
            + Proc.colors.reset.encode()
            + b'\n'
        ),
        call(
            Proc.prefix_colors[0].encode()
            # padding has been added because of output1
            + b'test_prefix '
            + Proc.colors.reset.encode()
            + b'| b'
            + Proc.colors.reset.encode()
            + b'\n'
        ),
    ]


@pytest.mark.asyncio
async def test_highlight():
    """
    Test that we can color output with regexps.
    """
    proc = await Proc(
        'echo hi',
        stdout=Mock(),
        regexps={
            r'h([\w\d-]+)': 'h{cyan}\\1',
        }
    ).wait()
    proc.stdout.buffer.write.assert_called_with(b'h\x1b[38;5;51mi\x1b[0m\n')


@pytest.mark.asyncio
async def test_highlight_if_not_colored():
    """
    Test that coloration does not apply on output that is already colored.
    """
    proc = await Proc(
        'echo -e h"\\e[31m"i',
        stdout=Mock(),
        regexps={
            r'h([\w\d-]+)': 'h{cyan}\\1',
        }
    ).wait()
    proc.stdout.buffer.write.assert_called_with(b'h\x1b[31mi\n')


@pytest.mark.asyncio
async def test_expect():
    proc = Proc(
        'sh', '-euc',
        'echo "x?"; read x; echo x=$x; echo "z?"; read z; echo z=$z',
        expects=[
            (b'x?', b'y\n'),
            (b'z?', b'w\n'),
        ],
        quiet=True,
    )
    await proc.wait()
    assert proc.out == 'x?\nx=y\nz?\nz=w'

@pytest.mark.asyncio
async def test_stderr():
    proc = await Proc(
        'sh',
        '-euc',
        'echo hi >&2',
        stdout=Mock(),
        stderr=Mock()
    ).wait()

    assert proc.err_raw == bytearray(b'hi\n')
    assert proc.err == 'hi'
    proc.stderr.buffer.write.assert_called_once_with(
        f'hi{proc.colors.reset}\n'.encode()
    )
