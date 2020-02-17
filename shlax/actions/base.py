from copy import deepcopy
import functools
import inspect
import importlib
import sys

from ..output import Output
from ..exceptions import WrongResult


class Action:
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
    )

    def __init__(self, *args, doc=None, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.call_args = []
        self.call_kwargs = {}
        self._doc = doc
        self.menu = {
            name: value
            for name, value in kwargs.items()
            if isinstance(value, Action)
        }

    @property
    def context(self):
        if not self.parent:
            if '_context' not in self.__dict__:
                self._context = dict()
            return self._context
        else:
            return self.parent.context

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

    def __getattr__(self, name):
        for a in self.parents() + self.sibblings() + self.children():
            if name in a.contextualize:
                return getattr(a, name)
        raise AttributeError(f'{type(self).__name__} has no {name}')

    async def call(self, *args, **kwargs):
        print(f'{self}.call(*args, **kwargs) not implemented')
        sys.exit(1)

    def output_factory(self, *args, **kwargs):
        kwargs.setdefault('regexps', self.regexps)
        return Output(**kwargs)

    async def __call__(self, *args, **kwargs):
        self.call_args = list(self.call_args) + list(args)
        self.call_kwargs.update(kwargs)
        self.output = self.output_factory(*args, **kwargs)
        self.output_start()
        self.status = 'running'
        try:
            result = await self.call(*args, **kwargs)
        except Exception as e:
            self.output_fail(e)
            self.status = 'fail'
            proc = getattr(e, 'proc', None)
            if proc:
                result = proc.rc
            else:
                raise
        else:
            self.output_success()
            if self.status == 'running':
                self.status = 'success'
        finally:
            clean = getattr(self, 'clean', None)
            if clean:
                self.output.clean(self)
                await clean(*args, **kwargs)
        return result

    def output_start(self):
        if self.kwargs.get('quiet', False):
            return
        self.output.start(self)

    def output_fail(self, exception=None):
        if self.kwargs.get('quiet', False):
            return
        self.output.fail(self, exception)

    def output_success(self):
        if self.kwargs.get('quiet', False):
            return
        self.output.success(self)

    def __repr__(self):
        return ' '.join([type(self).__name__] + list(self.args) + [
            f'{k}={v}'
            for k, v in self.kwargs.items()
        ])

    def colorized(self):
        return ' '.join([
            self.output.colors['pink1']
            + type(self).__name__
            + self.output.colors['yellow']
        ] + list(self.args) + [
            f'{self.output.colors["blue"]}{k}{self.output.colors["gray"]}={self.output.colors["green2"]}{v}'
            for k, v in self.kwargs_output().items()
        ] + [self.output.colors['reset']])

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
            import cli2
            a = cli2.Callable.factory(action).target
            if not a:
                a = cli2.Callable.factory(
                    '.'.join(['shlax', action])
                ).target
            if a:
                action = a

        p = action(*args, **kwargs)
        for parent in self.parents():
            if hasattr(parent, 'actions'):
                break
        p.parent = parent
        if 'actions' not in self.__dict__:
            # "mutate" to Strategy
            from ..strategies.script import Actions
            self.actions = Actions(self, [p])
        return p

    def bind(self, *args):
        clone = deepcopy(self)
        clone.call_args = args
        return clone
