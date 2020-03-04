from shlax.cli import ConsoleScript


def test_parser():
    parser = ConsoleScript.Parser(['@host'])
    parser.parse()
    assert parser.targets['host'] == Ssh('host')
