

class Output:
    colors = (
        '\x1b[1;36;45m',
        '\x1b[1;36;41m',
        '\x1b[1;36;40m',
        '\x1b[1;37;45m',
        '\x1b[1;32m',
        '\x1b[1;37;44m',
    )

    def __init__(self, prefix=None):
        self.prefix = prefix
        self.prefixes = dict()
        self.prefix_length = 0

    def call(self, line, prefix, highlight=True, flush=True):
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
        return line
