

class Run:
    def __init__(self, cmd):
        self.cmd = cmd

    async def __call__(self, target):
        target.exec(self.cmd)
