import asyncio

from shlax import Subprocess


async def main():
    colors = {
        '^(.*).txt$': '{green}\\1.txt',
        '^(.*).py$': '{bred}\\1.py',
    }
    await asyncio.gather(
        Subprocess(
            'for i in $(find .. | head); do echo $i; sleep .2; done',
            regexps=colors,
            prefix='parent',
        ).wait(),
        Subprocess(
            'for i in $(find . | head); do echo $i; sleep .3; done',
            regexps=colors,
            prefix='cwd',
        ).wait(),
    )

asyncio.run(main())
