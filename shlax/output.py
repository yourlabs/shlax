import re
import sys

from .colors import colors


class Output:
    prefixes = dict()
    colors = colors
    prefix_colors = (
        '\x1b[1;36;45m',
        '\x1b[1;36;41m',
        '\x1b[1;36;40m',
        '\x1b[1;37;45m',
        '\x1b[1;32m',
        '\x1b[1;37;44m',
    )

    def color(self, code=None):
        if not code:
            return '\u001b[0m'
        code = str(code)
        return u"\u001b[38;5;" + code + "m"

    def colorize(self, code, content):
        return self.color(code) + content + self.color()

    def colorized(self, action):
        if hasattr(action, 'colorized'):
            return action.colorized(self.colors)
        else:
            return str(action)

    def __init__(
            self,
            prefix=None,
            regexps=None,
            debug='cmd,visit,out',
            write=None,
            flush=None,
            **kwargs
        ):
        self.prefix = prefix
        self.debug = debug
        self.prefix_length = 0
        self.regexps = regexps or dict()
        self.write = write or sys.stdout.buffer.write
        self.flush = flush or sys.stdout.flush
        self.kwargs = kwargs

    def prefix_line(self):
        if self.prefix not in self.prefixes:
            self.prefixes[self.prefix] = self.prefix_colors[len(self.prefixes)]
            if len(self.prefix) > self.prefix_length:
                self.prefix_length = len(self.prefix)

        prefix_color = self.prefixes[self.prefix] if self.prefix else ''
        prefix_padding = '.' * (self.prefix_length - len(self.prefix) - 2) if self.prefix else ''
        if prefix_padding:
            prefix_padding = ' ' + prefix_padding + ' '

        return [
            prefix_color,
            prefix_padding,
            self.prefix,
            ' ',
            self.colors['reset'],
            '| '
        ]

    def __call__(self, line, highlight=True, flush=True):
        line = [self.highlight(line) if highlight else line]
        if self.prefix:
            line = self.prefix_line() + line
        line = ''.join(line)

        self.write(line.encode('utf8'))

        if flush:
            self.flush()

    def cmd(self, line):
        self(
            self.colorize(251, '+')
            + '\x1b[1;38;5;15m'
            + ' '
            + self.highlight(line, 'bash')
            + self.colors['reset']
            + '\n',
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
        line = line + self.colors['reset']

        return line

    def test(self, action):
        self(''.join([
            self.colors['purplebold'],
            '!  TEST   ',
            self.colors['reset'],
            self.colorized(action),
            '\n',
        ]))

    def clean(self, action):
        if self.debug:
            self(''.join([
                self.colors['bluebold'],
                '+  CLEAN  ',
                self.colors['reset'],
                self.colorized(action),
                '\n',
            ]))

    def start(self, action):
        if self.debug is True or 'visit' in str(self.debug):
            self(''.join([
                self.colors['orangebold'],
                '⚠  START  ',
                self.colors['reset'],
                self.colorized(action),
                '\n',
            ]))

    def skip(self, action):
        if self.debug is True or 'visit' in str(self.debug):
            self(''.join([
                self.colors['yellowbold'],
                '↪️ SKIP    ',
                self.colors['reset'],
                self.colorized(action),
                '\n',
            ]))

    def success(self, action):
        if self.debug is True or 'visit' in str(self.debug):
            self(''.join([
                self.colors['greenbold'],
                '✔ SUCCESS ',
                self.colors['reset'],
                self.colorized(action),
                '\n',
            ]))

    def fail(self, action, exception=None):
        if self.debug is True or 'visit' in str(self.debug):
            self(''.join([
                self.colors['redbold'],
                '✘  FAIL   ',
                self.colors['reset'],
                self.colorized(action),
                '\n',
            ]))

    def results(self, action):
        success = 0
        fail = 0
        for result in action.results:
            if result.status == 'success':
                success += 1
            if result.status == 'failure':
                fail += 1

        self(''.join([
            self.colors['greenbold'],
            '✔ SUCCESS REPORT: ',
            self.colors['reset'],
            str(success),
            '\n',
        ]))

        if fail:
            self(''.join([
                self.colors['redbold'],
                '✘  FAIL REPORT: ',
                self.colors['reset'],
                str(fail),
                '\n',
            ]))
