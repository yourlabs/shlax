import asyncio
import functools
import re
import sys

from .colors import colors


class SubprocessProtocol(asyncio.SubprocessProtocol):
    def __init__(self, proc):
        self.proc = proc
        self.output = bytearray()

    def pipe_data_received(self, fd, data):
        if fd == 1:
            self.proc.stdout(data)
        elif fd == 2:
            self.proc.stderr(data)

    def process_exited(self):
        self.proc.exit_future.set_result(True)


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
        write=None,
        flush=None,
    ):
        if len(args) == 1 and ' ' in args[0]:
            args = ['sh', '-euc', args[0]]

        self.cmd = ' '.join(args)
        self.args = args
        self.quiet = quiet if quiet is not None else False
        self.prefix = prefix
        self.write = write or sys.stdout.buffer.write
        self.flush = flush or sys.stdout.flush
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
        # Get a reference to the event loop as we plan to use
        # low-level APIs.
        loop = asyncio.get_running_loop()

        self.exit_future = asyncio.Future(loop=loop)

        # Create the subprocess controlled by DateProtocol;
        # redirect the standard output into a pipe.
        self.transport, self.protocol = await loop.subprocess_exec(
            lambda: SubprocessProtocol(self),
            *self.args,
            stdin=None,
        )
        self.started = True

    async def wait(self, *args, **kwargs):
        if not self.started:
            await self.start()

        if not self.waited:
            # Wait for the subprocess exit using the process_exited()
            # method of the protocol.
            await self.exit_future

            # Close the stdout pipe.
            self.transport.close()

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
