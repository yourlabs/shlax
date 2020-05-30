class Copy:
    def __init__(self, *args):
        self.src = args[:-1]
        self.dst = args[-1]

    @property
    def files(self):
        for root, dirs, files in os.walk(self.dst):
            pass


    async def __call__(self, target):
        await target.copy(*self.args)

    def __str__(self):
        return f'Copy(*{self.src}, {self.dst})'

    def cachehash(self):
        return str(self)
