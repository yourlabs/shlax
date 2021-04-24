

class Run:
    def __init__(self, cmd, root=False):
        self.cmd = cmd
        self.root = root

    async def __call__(self, target):
        if self.root:
            self.proc = await target.rexec(self.cmd)
        else:
            self.proc = await target.exec(self.cmd)

    def __str__(self):
        return f'Run({self.cmd})'
