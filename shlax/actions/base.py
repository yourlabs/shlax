import inspect
import sys


class Action:
    parent = None
    contextualize = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

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
        raise AttributeError(name)

    async def __call__(self, *args, **kwargs):
        print(f'{self}.__call__(*args, **kwargs) not implemented')
        sys.exit(1)
