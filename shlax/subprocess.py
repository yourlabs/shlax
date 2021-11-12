import asyncio
import functools
import os
import re
import shlex
import sys

from .colors import colors


class SubprocessProtocol(asyncio.subprocess.SubprocessStreamProtocol):
    def __init__(self, proc, *args, **kwargs):
        self.proc = proc
        super().__init__(*args, **kwargs)

    def receive(self, data, raw, target):
        raw.extend(data)
        if not self.proc.quiet:
            for line in self.proc.lines(data):
                target.buffer.write(line)
            target.flush()

    def pipe_data_received(self, fd, data):
        if fd == 1:
            self.receive(data, self.proc.out_raw, self.proc.stdout)
        elif fd == 2:
            self.receive(data, self.proc.err_raw, self.proc.stderr)

        if self.proc.expect_index < len(self.proc.expects):
            expected = self.proc.expects[self.proc.expect_index]
            if re.match(expected[0], data):
                self.stdin.write(expected[1])
                event_loop = asyncio.get_event_loop()
                asyncio.create_task(self.stdin.drain())
                self.proc.expect_index += 1


class Subprocess:
    colors = colors

    # arbitrary list of colors
    prefix_colors = (
        colors.cyan,
        colors.blue,
        colors.green,
        colors.purple,
        colors.red,
        colors.yellow,
        colors.gray,
        colors.pink,
        colors.orange,
    )

    # class variables, meant to grow as new prefixes are discovered to ensure
    # output alignment
    prefixes = dict()
    prefix_length = 0

    def __init__(
        self,
        *args,
        quiet=None,
        prefix=None,
        regexps=None,
        expects=None,
        write=None,
        flush=None,
        stdout=None,
        stderr=None,
    ):
        self.args = args
        self.quiet = quiet if quiet is not None else False
        self.prefix = prefix
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.expects = expects or []
        self.expect_index = 0
        self.started = False
        self.waited = False
        self.out_raw = bytearray()
        self.err_raw = bytearray()

        self.regexps = dict()
        if regexps:
            for search, replace in regexps.items():
                if isinstance(search, str):
                    search = search.encode()
                search = re.compile(search)
                replace = replace.format(**self.colors.__dict__).encode()
                self.regexps[search] = replace

    async def start(self, wait=True):
        if len(self.args) == 1 and not os.path.exists(self.args[0]):
            args = shlex.split(self.args[0])
        else:
            args = self.args

        if not self.quiet:
            message = b''.join([
                self.colors.bgray.encode(),
                b'+ ',
                shlex.join(args).replace('\n', '\\n').encode(),
                self.colors.reset.encode(),
            ])
            for line in self.lines(message, highlight=False):
                self.stdout.buffer.write(line)
            self.stdout.flush()

        # The following is a copy of what asyncio.subprocess_exec and
        # asyncio.create_subprocess_exec do except we inject our own
        # SubprocessStreamProtocol subclass: it might need an update as new
        # python releases come out.
        loop = asyncio.get_running_loop()

        self.transport, self.protocol = await loop.subprocess_exec(
            lambda: SubprocessProtocol(
                self,
                limit=asyncio.subprocess.streams._DEFAULT_LIMIT,
                loop=loop,
            ),
            *args,
            stdin=asyncio.subprocess.PIPE if self.expects else sys.stdin,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.proc = asyncio.subprocess.Process(self.transport, self.protocol, loop)
        self.started = True

    async def wait(self, *args, **kwargs):
        if not self.started:
            await self.start()

        if not self.waited:
            await self.proc.communicate()
            self.rc = self.transport.get_returncode()
            self.waited = True

        return self

    @property
    def out(self):
        if self.waited:
            if '_out_cached' not in self.__dict__:
                self._out_cached = self.out_raw.decode().strip()
            return self._out_cached
        return self.out_raw.decode().strip()

    @property
    def err(self):
        if self.waited:
            if '_err_cached' not in self.__dict__:
                self._err_cached = self.err_raw.decode().strip()
            return self._err_cached
        return self.err_raw.decode().strip()

    def lines(self, data, highlight=True):
        for line in data.strip().split(b'\n'):
            line = [self.highlight(line) if highlight else line]
            if self.prefix:
                line = self.prefix_line() + line
            line.append(b'\n')
            yield b''.join(line)

    def highlight(self, line, highlight=True):
        if not highlight or (
            b'\x1b[' in line
            or b'\033[' in line
            or b'\\e[' in line
        ):
            return line

        for search, replace in self.regexps.items():
            line = re.sub(search, replace, line)
        line = line + self.colors.reset.encode()

        return line

    def prefix_line(self):
        if self.prefix not in self.prefixes:
            self.prefixes[self.prefix] = self.prefix_colors[len(self.prefixes)]
            if len(self.prefix) > self.prefix_length:
                type(self).prefix_length = len(self.prefix)

        return [
            self.prefixes[self.prefix].encode(),
            b' ' * (self.prefix_length - len(self.prefix)),
            self.prefix.encode(),
            b' ',
            self.colors.reset.encode(),
            b'| '
        ]
