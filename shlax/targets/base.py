import copy

from ..result import Result, Results


class Target:
    def __init__(self, *actions, **options):
        self.actions = actions
        self.options = options
        self.results = []

    async def __call__(self, *actions):
        for action in actions or self.actions:
            try:
                await action(self)
            except Exception as e:
                action.status = 'failure'
                action.exception = e
                if actions:
                    # nested call, re-raise
                    raise
                else:
                    break
            else:
                action.status = 'success'
            finally:
                self.results.append(action)
