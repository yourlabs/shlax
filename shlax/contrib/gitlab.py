import yaml

from shlax import *


class GitLabCIConfig(Script):
    async def call(self, *args, write=True, **kwargs):
        output = yaml.dump(self.kwargs)
        self.output(output)
        if write:
            with open('.gitlab-ci.yml', 'w+') as f:
                f.write(output)
