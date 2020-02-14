from shlax import *

inner = Run()
other = Run('ls')
middle = Buildah('alpine', inner, other)
outer = Localhost(middle)


def test_action_init_args():
    assert other.args == ('ls',)


def test_action_parent_autoset():
    assert list(outer.actions) == [middle]
    assert middle.parent == outer
    assert inner.parent == middle
    assert other.parent == middle


def test_action_context():
    assert outer.context is inner.context
    assert middle.context is inner.context
    assert middle.context is outer.context
    assert other.context is outer.context


def test_action_sibblings():
    assert inner.sibblings() == [other]
    assert inner.sibblings(lambda s: s.args[0] == 'ls') == [other]
    assert inner.sibblings(lambda s: s.args[0] == 'foo') == []
    assert inner.sibblings(type='run') == [other]
    assert inner.sibblings(args=('ls',)) == [other]


def test_actions_parents():
    assert other.parents() == [middle, outer]
    assert other.parents(lambda p: p.base == 'alpine') == [middle]
    assert inner.parents(type='localhost') == [outer]
    assert inner.parents(type='buildah') == [middle]


def test_action_childrens():
    assert middle.children() == [inner, other]
    assert middle.children(lambda a: a.args[0] == 'ls') == [other]
    assert outer.children() == [middle, inner, other]


def test_action_getattr():
    assert other.exec == middle.exec
    assert other.shargs == middle.shargs
