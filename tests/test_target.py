import pytest

from shlax.targets.stub import Stub
from shlax.actions.run import Run
from shlax.actions.parallel import Parallel
from shlax.result import Result


class Error:
    async def __call__(self, target):
        raise Exception('lol')


@pytest.mark.asyncio
async def test_success():
    action = Run('echo hi')
    target = Stub(action)
    await target()
    assert target.results[0].action == action
    assert target.results[0].status == 'success'


@pytest.mark.asyncio
async def test_error():
    action = Error()
    target = Stub(action)
    await target()
    assert target.results[0].action == action
    assert target.results[0].status == 'failure'


@pytest.mark.asyncio
async def test_nested():
    nested = Error()

    class Nesting:
        async def __call__(self, target):
            await target(nested)
    nesting = Nesting()

    target = Stub(nesting)
    await target()

    assert len(target.results) == 2
    assert target.results[0].status == 'failure'
    assert target.results[0].action == nested
    assert target.results[1].status == 'failure'
    assert target.results[1].action == nesting


@pytest.mark.asyncio
async def test_parallel():
    winner = Run('echo hi')
    looser = Error()
    parallel = Parallel(winner, looser)

    target = Stub(parallel)
    await target()
    assert len(target.results) == 3
    assert target.results[0].status == 'success'
    assert target.results[0].action == winner
    assert target.results[1].status == 'failure'
    assert target.results[1].action == looser
    assert target.results[2].status == 'failure'
    assert target.results[2].action == parallel


@pytest.mark.asyncio
async def test_function():
    async def hello(target):
        await target.exec('hello')
    await Stub()(hello)


@pytest.mark.asyncio
async def test_action_clean():
    class Example:
        def __init__(self):
            self.was_called = False
        async def clean(self, target, result):
            self.was_called = True
        async def __call__(self, target):
            raise Exception('lol')

    action = Example()
    target = Stub()
    with pytest.raises(Exception):
        await target(action)
    assert action.was_called


@pytest.mark.asyncio
async def test_target_clean():
    class Example(Stub):
        def __init__(self, action):
            self.was_called = False
            super().__init__(action)
        async def clean(self, target, result):
            self.was_called = True

    target = Example(Error())
    await target()
    assert target.was_called


@pytest.mark.asyncio
async def test_method():
    class Example:
        def __init__(self):
            self.was_called = False
        async def test(self, target):
            self.was_called = True

    example = Example()
    action = example.test
    target = Stub()
    await target(action)
    assert example.was_called


@pytest.mark.asyncio
async def test_target_action():
    child = Stub(Run('echo hi'))
    parent = Stub(child)

    grandpa = Stub()
    await grandpa(parent)
    assert len(grandpa.results) == 3

    grandpa = Stub(parent)
    await grandpa()
    assert len(grandpa.results) == 3
