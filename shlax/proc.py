"""
Asynchronous process execution wrapper.
"""

import asyncio
import os
import shlex
import sys

from .output import Output


class ProcFailure(Exception):
    def __init__(self, proc):
        self.proc = proc

        msg = f'FAIL exit with {proc.rc} ' + proc.args[0]

        if not proc.output.debug or 'cmd' not in str(proc.output.debug):
            msg += '\n' + proc.cmd

        if not proc.output.debug or 'out' not in str(proc.output.debug):
            msg += '\n' + proc.out
            msg += '\n' + proc.err

        super().__init__(msg)


class PrefixStreamProtocol(asyncio.subprocess.SubprocessStreamProtocol):
    """
    Internal subprocess stream protocol to add a prefix in front of output to
    make asynchronous output readable.
    """

    def __init__(self, proc, *args, **kwargs):
        self.proc = proc
        super().__init__(*args, **kwargs)

    def pipe_data_received(self, fd, data):
        if self.proc.output.debug is True or 'out' in str(self.proc.output.debug):
            if fd in (1, 2):
                self.proc.output(data)
        super().pipe_data_received(fd, data)


def protocol_factory(proc):
    def _p():
        return PrefixStreamProtocol(
            proc,
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

    def __init__(self, *args, prefix=None, raises=True, output=None, quiet=False):
        if quiet:
            self.output = Output(debug=False)
        else:
            self.output = output or Output()
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

    def output_factory(self, *args, **kwargs):
        args = tuple(self.prefix) + args
        return Output(*args, kwargs)

    async def __call__(self, wait=True):
        if self.called:
            raise Exception('Already called: ' + self.cmd)

        if 'cmd' in str(self.output.debug):
            self.output.cmd(self.cmd)

        if self.test:
            if self.test is True:
                type(self).test = []
            self.test.append(self.args)
            return self

        loop = asyncio.events.get_event_loop()
        transport, protocol = await loop.subprocess_exec(
            protocol_factory(self), *self.args)
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
            raise ProcFailure(self)
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
