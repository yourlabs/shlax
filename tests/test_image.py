import pytest
import os

from shlax import Image


tests = {
    'docker://a.b:1337/re/po:x,y': ('docker', 'a.b:1337', 're/po', 'x,y'),
    'docker://a.b/re/po:x,y': ('docker', 'a.b', 're/po', 'x,y'),
    'a.b:1337/re/po:x,y': (None, 'a.b:1337', 're/po', 'x,y'),
    'a.b/re/po:x,y': (None, 'a.b', 're/po', 'x,y'),
    're/po:x,y': (None, None, 're/po', 'x,y'),
    're/po': (None, None, 're/po', 'latest'),
    'docker://re/po': ('docker', None, 're/po', 'latest'),
    'docker://re/po:x,y': ('docker', None, 're/po', 'x,y'),
}

@pytest.mark.parametrize(
    'arg,expected', [(k, dict(
        backend=v[0], registry=v[1], repository=v[2], tags=v[3].split(',')
    )) for k, v in tests.items()]
)
def test_args(arg, expected):
    Image.ENV_TAGS = []
    im = Image(arg)
    for k, v in expected.items():
        assert getattr(im, k) == v

def test_args_env():
    os.environ['IMAGE_TEST_ARGS_ENV'] = 'foo'
    Image.ENV_TAGS = ['IMAGE_TEST_ARGS_ENV']
    im = Image('re/po:x,y')
    assert im.tags == ['x', 'y', 'foo']
