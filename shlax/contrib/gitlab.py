import yaml

from shlax import *


class GitLabCIConfig(Script):
    async def call(self, *args, write=True, **kwargs):
        output = yaml.dump(self.kwargs)
        if kwargs['debug'] is True:
            self.output(output)
        if write:
            with open('.gitlab-ci.yml', 'w+') as f:
                f.write(output)

    def colorized(self):
        return type(self).__name__
