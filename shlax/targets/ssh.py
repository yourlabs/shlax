from .base import Target


class Ssh(Target):
    def __init__(self, *actions, host, user=None):
        self.host = host
        self.user = user
        super().__init__(*actions)

    async def exec(self, *args, user=None, **kwargs):
        _args = ['ssh', self.host]
        if user == 'root':
            _args += ['sudo']
        _args += [' '.join([str(a) for a in args])]
        return await self.parent.exec(*_args, **kwargs)
