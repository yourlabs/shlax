"""
Asynchronous process execution wrapper.
"""

import asyncio
from colorama import Fore, Back, Style
import os
import shlex
import sys

from .exceptions import WrongResult
import pygments
from pygments import lexers
from pygments.formatters import TerminalFormatter
from pygments.formatters import Terminal256Formatter


class Output:
    colors = (
        '\x1b[1;36;45m',
        '\x1b[1;36;41m',
        '\x1b[1;36;40m',
        '\x1b[1;37;45m',
        '\x1b[1;32m',
        '\x1b[1;37;44m',
    )
    def __init__(self):
        self.prefixes = dict()
        self.prefix_length = 0

    def __call__(self, line, prefix, highlight=True, flush=True):
        if prefix and prefix not in self.prefixes:
            self.prefixes[prefix] = (
                self.colors[len([*self.prefixes.keys()]) - 1]
            )
            if len(prefix) > self.prefix_length:
                self.prefix_length = len(prefix)

        prefix_color = self.prefixes[prefix] if prefix else ''
        prefix_padding = '.' * (self.prefix_length - len(prefix) - 2) if prefix else ''
        if prefix_padding:
            prefix_padding = ' ' + prefix_padding + ' '

        sys.stdout.buffer.write((
            (
                prefix_color
                + prefix_padding
                + prefix
                + ' '
                + Back.RESET
                + Style.RESET_ALL
                + Fore.LIGHTBLACK_EX
                + '| '
                + Style.RESET_ALL
                if prefix
                else ''
            )
            + self.highlight(line, highlight)
        ).encode('utf8'))

        if flush:
            sys.stdout.flush()

    def cmd(self, line, prefix):
        self(
            Fore.LIGHTBLACK_EX
            + '+ '
            + Style.RESET_ALL
            + self.highlight(line, 'bash'),
            prefix,
            highlight=False
        )

    def print(self, content):
        self(
            content,
            prefix=None,
            highlight=False
        )

    def highlight(self, line, highlight=True):
        line = line.decode('utf8') if isinstance(line, bytes) else line
        if not highlight or (
            '\x1b[' in line
            or '\033[' in line
            or '\\e[' in line
        ):
            return line
        elif isinstance(highlight, str):
            lexer = lexers.get_lexer_by_name(highlight)
        else:
            lexer = lexers.get_lexer_by_name('python')
        formatter = Terminal256Formatter(
            style=os.getenv('PODCTL_STYLE', 'fruity'))
        return pygments.highlight(line, lexer, formatter)


output = Output()


class PrefixStreamProtocol(asyncio.subprocess.SubprocessStreamProtocol):
    """
    Internal subprocess stream protocol to add a prefix in front of output to
    make asynchronous output readable.
    """

    def __init__(self, prefix, *args, **kwargs):
        self.debug = kwargs.get('debug', True)
        self.prefix = prefix
        super().__init__(*args, **kwargs)

    def pipe_data_received(self, fd, data):
        if (self.debug is True or 'out' in str(self.debug)) and fd in (1, 2):
            output(data, self.prefix, flush=False)
            sys.stdout.flush()
        super().pipe_data_received(fd, data)


def protocol_factory(prefix):
    def _p():
        return PrefixStreamProtocol(
            prefix,
            limit=asyncio.streams._DEFAULT_LIMIT,
            loop=asyncio.events.get_event_loop()
        )
    return _p


class Proc:
    """
    Subprocess wrapper.

    Example usage::

        proc = Proc('find', '/', prefix='containername')

        await proc()     # execute

        print(proc.out)  # stdout
        print(proc.err)  # stderr
        print(proc.rc)   # return code
    """
    test = False

    def __init__(self, *args, prefix=None, raises=True, debug=True):
        self.debug = debug if not self.test else False
        self.cmd = ' '.join(args)
        self.args = args
        self.prefix = prefix
        self.raises = raises
        self.called = False
        self.communicated = False
        self.out_raw = b''
        self.err_raw = b''
        self.out = ''
        self.err = ''
        self.rc = None

    @staticmethod
    def split(*args):
        args = [str(a) for a in args]
        if len(args) == 1:
            if isinstance(args[0], (list, tuple)):
                args = args[0]
            else:
                args = ['sh', '-euc', ' '.join(args)]
        return args

    async def __call__(self, wait=True):
        if self.called:
            raise Exception('Already called: ' + self.cmd)

        if self.debug is True or 'cmd' in str(self.debug):
            output.cmd(self.cmd, self.prefix)

        if self.test:
            if self.test is True:
                type(self).test = []
            self.test.append(self.args)
            return self

        loop = asyncio.events.get_event_loop()
        transport, protocol = await loop.subprocess_exec(
            protocol_factory(self.prefix), *self.args)
        self.proc = asyncio.subprocess.Process(transport, protocol, loop)
        self.called = True

        if wait:
            await self.wait()

        return self

    async def communicate(self):
        self.out_raw, self.err_raw = await self.proc.communicate()
        self.out = self.out_raw.decode('utf8').strip()
        self.err = self.err_raw.decode('utf8').strip()
        self.rc = self.proc.returncode
        self.communicated = True
        return self

    async def wait(self):
        if self.test:
            return self
        if not self.called:
            await self()
        if not self.communicated:
            await self.communicate()
        if self.raises and self.proc.returncode:
            raise WrongResult(self)
        return self

    @property
    def json(self):
        import json
        return json.loads(self.out)

    def mock():
        """Context manager for testing purpose."""
        cls = Proc
        class Mock:
            def __enter__(_):
                cls.test = True
            def __exit__(_, exc_type, exc_value, traceback):
                cls.test = False
        return Mock()
