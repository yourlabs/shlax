import yaml

from shlax import *


class GitLabCIConfig(Script):
    async def __call__(self, *args, write=True, **kwargs):
        await super().__call__(*args, **kwargs)
        self.kwargs = kwargs
        for name, definition in self.context.items():
            self.kwargs[name] = definition
        output = yaml.dump(self.kwargs)
        print(output)
        if write:
            with open('.gitlab-ci.yml', 'w+') as f:
                f.write(output)


class Job(Action):
    async def __call__(self, *args, **kwargs):
        self.context[self.args[0]] = self.kwargs
