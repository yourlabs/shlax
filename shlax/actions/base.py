from copy import deepcopy
import functools
import inspect
import importlib
import sys

from ..output import Output
from ..exceptions import WrongResult
from ..result import Result


class class_or_instance_method:
    def __init__(self, f):
        self.f = f

    def __get__(self, instance, owner):
        def newfunc(*args, **kwargs):
            return self.f(
                instance if instance is not None else owner,
                *args,
                **kwargs
            )
        return newfunc


class Action:
    display_variables = []
    hide_variables = ['output']
    default_steps = ['apply']
    parent = None
    contextualize = []
    regexps = {
        r'([\w]+):': '{cyan}\\1{gray}:{reset}',
        r'(^|\n)( *)\- ': '\\1\\2{red}-{reset} ',
    }
    options = dict(
        debug=dict(
            alias='d',
            default='visit',
            help='''
            Display debug output. Supports values (combinable): cmd,out,visit
            '''.strip(),
            immediate=True,
        ),
        v=dict(
            default=False,
            help='Verbose, like -d=visit,cmd,out',
            immediate=True,
        ),
    )

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
            if isinstance(value, Action):
                getattr(self, key).shlaxstep = True

    def actions_filter(self, results, f=None, **filters):
        if f:
            def ff(a):
                try:
                    return f(a)
                except:
                    return False
            results = [*filter(ff, results)]

        for k, v in filters.items():
            if k == 'type':
                results = [*filter(
                    lambda s: type(s).__name__.lower() == str(v).lower(),
                    results
                )]
            else:
                results = [*filter(
                    lambda s: getattr(s, k, None) == v,
                    results
                )]

        return results


    def sibblings(self, f=None, **filters):
        if not self.parent:
            return []
        return self.actions_filter(
            [a for a in self.parent.actions if a is not self],
            f, **filters
        )

    def parents(self, f=None, **filters):
        if self.parent:
            return self.actions_filter(
                [self.parent] + self.parent.parents(),
                f, **filters
            )
        return []

    def children(self, f=None, **filters):
        children = []
        def add(parent):
            if parent != self:
                children.append(parent)
            if 'actions' not in parent.__dict__:
                return

            for action in parent.actions:
                add(action)
        add(self)
        return self.actions_filter(children, f, **filters)

    async def __call__(self, *targets, **options):
        if not targets:
            from ..targets.localhost import Localhost
            targets = [Localhost()]

        output = Output(
            regexp=self.regexps,
            debug='cmd,visit,out' if options['v'] else options['debug'],
        )
        results = []
        for target in targets:
            target.output = output
            if len(targets) > 1:
                output.prefix = target
            from copy import deepcopy
            action = deepcopy(self)
            action.target = target
            result = Result(action, target)
            results.append(result)
            action.result = result
            action.output = output
            for step in options.get('steps', None) or self.default_steps:
                if step not in action.steps():
                    print(f'Failed to find {type(action).__name__}.{step}')
                    continue
                action.step = step
                output.start(action)
                try:
                    if isinstance(getattr(action, step), Action):
                        await getattr(action, step)(**options)
                    else:
                        await getattr(action, step)()
                except Exception as e:
                    output.fail(action, e)
                    action.result.status = 'fail'
                    proc = getattr(e, 'proc', None)
                    if proc:
                        result = proc.rc
                    else:
                        raise
                else:
                    output.success(action)
                    result.status = 'success'
                finally:
                    clean = getattr(action, 'clean', None)
                    if clean:
                        output.clean(action)
                        await clean(target)

        return results

    def __repr__(self):
        return ' '.join([type(self).__name__] + [
            f'{k}={v}'
            for k, v in self.__dict__.items()
            if (k in self.display_variables or not self.display_variables)
            and (k not in self.hide_variables)
        ])

    def colorized(self, colors):
        return ' '.join([
            colors['pink1']
            + type(self).__name__
            + '.'
            + self.step
            + colors['yellow']
        ] + [
            f'{colors["blue"]}{k}{colors["gray"]}={colors["green2"]}{v}'
            for k, v in self.__dict__.items()
            if (k in self.display_variables or not self.display_variables)
            and (k not in self.hide_variables)
        ] + [colors['reset']])

    def callable(self):
        from ..targets import Localhost
        async def cb(*a, **k):
            from shlax.cli import cli
            script = Localhost(self, quiet=True)
            result = await script(*a, **k)

            success = functools.reduce(
                lambda a, b: a + b,
                [1 for c in script.children() if c.status == 'success'] or [0])
            if success:
                script.output.success(f'{success} PASS')

            failures = functools.reduce(
                lambda a, b: a + b,
                [1 for c in script.children() if c.status == 'fail'] or [0])
            if failures:
                script.output.fail(f'{failures} FAIL')
            cli.exit_code = failures
            return result
        return cb

    def kwargs_output(self):
        return self.kwargs

    def action(self, action, *args, **kwargs):
        if isinstance(action, str):
            # import dotted module path string to action
            import cli2
            a = cli2.Callable.factory(action).target
            if not a:
                a = cli2.Callable.factory(
                    '.'.join(['shlax', action])
                ).target
            if a:
                action = a

        p = action(*args, **kwargs)
        p.parent = self
        for parent in self.parents():
            if hasattr(parent, 'actions'):
                p.parent = parent
                break

        if 'actions' not in self.__dict__:
            # "mutate" to Strategy
            from ..strategies.script import Actions
            self.actions = Actions(self, [p])
        return p

    @class_or_instance_method
    def steps(self):
        return {
            key: getattr(self, key)
            for key in dir(self)
            if key != 'steps'  # avoid recursion
            and (
                key in self.default_steps
                or getattr(getattr(self, key), 'shlaxstep', False)
            )
        }
