import re
import sys

from .colors import colors


class Output:
    prefixes = dict()
    colors = colors

    def color(self, code=None):
        if not code:
            return '\u001b[0m'
        code = str(code)
        return u"\u001b[38;5;" + code + "m"

    def colorize(self, code, content):
        return self.color(code) + content + self.color()

    def __init__(self, prefix=None, regexps=None, debug=True, write=None, flush=None):
        self.prefix = prefix
        self.debug = debug
        self.prefix_length = 0
        self.regexps = regexps or dict()
        self.write = write or sys.stdout.buffer.write
        self.flush = flush or sys.stdout.flush

    def __call__(self, line, highlight=True, flush=True):
        if self.prefix and self.prefix not in self.prefixes:
            self.prefixes[self.prefix] = (
                self.colors[len([*self.prefixes.keys()]) - 1]
            )
            if len(self.prefix) > self.prefix_length:
                self.prefix_length = len(self.prefix)

        prefix_color = self.prefixes[self.prefix] if self.prefix else ''
        prefix_padding = '.' * (self.prefix_length - len(self.prefix) - 2) if self.prefix else ''
        if prefix_padding:
            prefix_padding = ' ' + prefix_padding + ' '

        self.write((
            (
                prefix_color
                + prefix_padding
                + self.prefix
                + ' '
                + '| '
                if self.prefix
                else ''
            )
            + self.highlight(line, highlight)
            + self.colors['reset']
        ).encode('utf8'))

        if flush:
            self.write(b'\n')
            self.flush()

    def cmd(self, line):
        self(
            self.colorize(251, '+')
            + '\x1b[1;38;5;15m'
            + ' '
            + self.highlight(line, 'bash')
            + self.colors['reset'],
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

        for regexp, colors in self.regexps.items():
            line = re.sub(regexp, colors.format(**self.colors), line)

        return line

    def start(self, action):
        self(''.join([
            self.colors['orange'],
            '[!] START ',
            self.colors['reset'],
            action.colorized(),
        ]))

    def success(self, action):
        self(''.join([
            self.colors['green'],
            '[√] SUCCESS ',
            self.colors['reset'],
            action.colorized(),
        ]))

    def fail(self, action, exception=None):
        self(''.join([
            self.colors['red'],
            '[x] FAIL ',
            self.colors['reset'],
            action.colorized(),
        ]))
