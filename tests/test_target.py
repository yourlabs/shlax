import pytest

from shlax.targets.base import Target
from shlax.actions.run import Run
from shlax.actions.parallel import Parallel
from shlax.result import Result


class Error:
    async def __call__(self, target):
        raise Exception('lol')


class Target(Target):
    def exec(self, *args):
        print(*args)


@pytest.mark.asyncio
async def test_success():
    action = Run('echo hi')
    target = Target(action)
    await target()
    assert action.status == 'success'


@pytest.mark.asyncio
async def test_error():
    action = Error()
    target = Target(action)
    await target()
    assert action.status == 'failure'


@pytest.mark.asyncio
async def test_nested():
    nested = Error()

    class Nesting:
        async def __call__(self, target):
            await target(nested)
    nesting = Nesting()

    target = Target(nesting)
    await target()

    assert len(target.results) == 2
    assert target.results == [nested, nesting]
    assert target.results[0].status == 'failure'
    assert target.results[1].status == 'failure'


@pytest.mark.asyncio
async def test_parallel():
    winner = Run('echo hi')
    looser = Error()
    parallel = Parallel(winner, looser)

    target = Target(parallel)
    await target()
    assert len(target.results) == 3
    assert target.results[0].status == 'success'
    assert target.results[0] == winner
    assert target.results[1].status == 'failure'
    assert target.results[1] == looser
    assert target.results[2].status == 'failure'
    assert target.results[2] == parallel
