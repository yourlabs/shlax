

class Run:
    def __init__(self, cmd):
        self.cmd = cmd

    async def __call__(self, target):
        self.proc = await target.exec(self.cmd)

    def __str__(self):
        return f'Run({self.cmd})'
