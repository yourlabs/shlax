import pytest
from shlax import Output


class Write:
    def __init__(self):
        self.output = ''
    def __call__(self, out):
        self.output += out.decode('utf8')


@pytest.fixture
def write():
    return Write()


def test_output_regexps(write):
    output = Output(
        regexps={'.*': {0: 0}},
        write=write,
        flush=lambda: None,
    )
    output('foo')
    assert write.output == output.colorize(0, 'foo')
