import yaml

from shlax import *


class GitLabCI(Script):
    async def call(self, *args, write=True, **kwargs):
        output = dict()
        for key, value in self.kwargs.items():
            if isinstance(value, dict):
                output[key] = value
                output[key]['script'] = './shlaxfile.py ' + key
            else:
                output[key] = value
        output = yaml.dump(output)
        if kwargs['debug'] is True:
            self.output(output)
        if write:
            with open('.gitlab-ci.yml', 'w+') as f:
                f.write(output)

    def colorized(self):
        return type(self).__name__
