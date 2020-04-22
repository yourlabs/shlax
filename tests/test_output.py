import pytest
from shlax.output import Output


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
        regexps={'^(.*)$': '{red}\\1'},
        write=write,
        flush=lambda: None,
    )
    output('foo')
    assert write.output.strip() == output.colors['red'] + 'foo' + output.colors['reset']
