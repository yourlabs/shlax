from copy import deepcopy
import yaml

from shlax import *


class GitLabCI(Script):
    async def call(self, *args, write=True, **kwargs):
        output = dict()
        for key, value in self.kwargs.items():
            if isinstance(value, dict):
                output[key] = deepcopy(value)
                image = output[key].get('image', 'alpine')
                if hasattr(image, 'image'):
                    output[key]['image'] = image.image.repository + ':$CI_COMMIT_SHORT_SHA'
            else:
                output[key] = value

        output = yaml.dump(output)
        if kwargs['debug'] is True:
            self.output(output)
        if write:
            with open('.gitlab-ci.yml', 'w+') as f:
                f.write(output)

        from shlax.cli import cli
        for arg in args:
            job = self.kwargs[arg]
            _args = []
            if not isinstance(job['image'], str):
                image = str(job['image'].image)
            else:
                image = job['image']
            await self.action('Docker', Run(job['script']), image=image)(*_args, **kwargs)

    def colorized(self):
        return type(self).__name__
