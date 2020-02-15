import yaml

from shlax import *


class GitLabCIConfig(Script):
    async def call(self, *args, write=True, **kwargs):
        self.context['definition'] = kwargs
        await super().call(*args, **kwargs)
        for name, definition in self.context['definition'].items():
            self.context['definition'][name] = definition
        output = yaml.dump(self.context['definition'])
        self.output(output)
        if write:
            with open('.gitlab-ci.yml', 'w+') as f:
                f.write(output)


class Job(Action):
    async def call(self, *args, **kwargs):
        self.context['definition'][self.args[0]] = self.kwargs

    def output_start(self):
        pass

    def output_success(self):
        pass
