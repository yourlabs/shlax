import json


class Podman(list):
    def __init__(self, target, *args):
        self.target = target
        super().__init__(args or ['podman'])

    def __getattr__(self, command):
        if command.startswith('_'):
            return super().__getattr__(command)
        return Podman(self.target, *self + [command])

    async def __call__(self, *args, **kwargs):
        cmd = self + list(args) + [
            f'--{k}={v}' for k, v in kwargs.items()
        ]
        if 'ps' in cmd:
            cmd += ['--format=json']
        return (await self.target.exec(*cmd, quiet=True)).json
