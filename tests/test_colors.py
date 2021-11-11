import shlax


def test_colors():
    assert shlax.colors.cyan == '\u001b[38;5;51m'
    assert shlax.colors.bcyan == '\u001b[1;38;5;51m'
    assert shlax.colors.reset == '\u001b[0m'
