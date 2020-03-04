import copy


class Action:
    args = dict(
        step=None,
    )


class
        user=dict(
            doc='Username',
            required=True,
        ),
        steps=dict(
            up='Started',
            down='Stopped',
        ),
    )


    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        pass


class Target(Action):
    def __call__(self, action):
        action = copy.deepcopy(action)
        action.target = self


class FakeAction(Action):


    def __init__(self, user, path, *steps, **kwargs)
        self.user = user
        self.path = path
        self.steps = steps
        self.kwargs = kwargs


action = Action('root', '/test', 'up', 'rm')
target = Target()
