import copy
import os

from ..exceptions import WrongResult
from ..actions.base import Action
from ..proc import Proc


class Actions(list):
    def __init__(self, owner, actions):
        self.owner = owner
        super().__init__()
        for action in actions:
            self.append(action)

    def append(self, value):
        value = copy.deepcopy(value)
        value.parent = self.owner
        value.status = 'pending'
        super().append(value)


class Script(Action):
    contextualize = ['shargs', 'exec', 'rexec', 'env', 'which', 'copy']

    def __init__(self, *actions, **kwargs):
        super().__init__(**kwargs)
        self.actions = Actions(self, actions)

    async def call(self, *args, **kwargs):
        for action in self.actions:
            await action(*args, **kwargs)
