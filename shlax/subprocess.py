import asyncio
import functools
import re
import shlex
import sys

from .colors import colors


class SubprocessProtocol(asyncio.subprocess.SubprocessStreamProtocol):
    def __init__(self, proc, *args, **kwargs):
        self.proc = proc
        super().__init__(*args, **kwargs)

    def pipe_data_received(self, fd, data):
        if fd == 1:
            self.proc.stdout(data)
        elif fd == 2:
            self.proc.stderr(data)

        if self.proc.expect_index < len(self.proc.expects):
            expected = self.proc.expects[self.proc.expect_index]
            if re.match(expected['regexp'], data):
                self.stdin.write(expected['sendline'])
                self.stdin.flush()
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
        cmd,
        quiet=None,
        prefix=None,
        regexps=None,
        expects=None,
        write=None,
        flush=None,
    ):
        self.cmd = cmd
        self.quiet = quiet if quiet is not None else False
        self.prefix = prefix
        self.write = write or sys.stdout.buffer.write
        self.flush = flush or sys.stdout.flush
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
        if not self.quiet:
            self.output(
                self.colors.bgray.encode()
                + b'+ '
                + self.cmd.encode()
                + self.colors.reset.encode(),
                highlight=False
            )

        # The following is a copy of what asyncio.create_subprocess_shell does
        # except we inject our own SubprocessStreamProtocol subclass: it might
        # need an update as new python releases come out.
        loop = asyncio.get_running_loop()
        self.transport, self.protocol = await loop.subprocess_shell(
            lambda: SubprocessProtocol(
                self,
                limit=asyncio.subprocess.streams._DEFAULT_LIMIT,
                loop=loop,
            ),
            self.cmd,
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
            self.waited = True

        return self

    def stdout(self, data):
        self.out_raw.extend(data)
        if not self.quiet:
            self.output(data)

    def stderr(self, data):
        self.err_raw.extend(data)
        if not self.quiet:
            self.output(data)

    @functools.cached_property
    def out(self):
        return self.out_raw.decode().strip()

    @functools.cached_property
    def err(self):
        return self.err_raw.decode().strip()

    @functools.cached_property
    def rc(self):
        return self.transport.get_returncode()

    def output(self, data, highlight=True, flush=True):
        for line in data.strip().split(b'\n'):
            line = [self.highlight(line) if highlight else line]
            if self.prefix:
                line = self.prefix_line() + line
            line.append(b'\n')
            line = b''.join(line)
            self.write(line)

        if flush:
            self.flush()

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
