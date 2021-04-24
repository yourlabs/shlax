import asyncio
import binascii
import glob
import os

from ..exceptions import ShlaxException


class Copy:
    def __init__(self, *args):
        self.dst = args[-1]
        self.src = []

        for src in args[:-1]:
            if '*' in src:
                self.src += glob.glob(src)
            else:
                self.src.append(src)

    async def listfiles(self, target):
        if getattr(self, '_listfiles', None):
            return self._listfiles

        result = []
        for src in self.src:
            if not await target.parent.exists(src):
                target.output.fail(self)
                raise ShlaxException(f'File not found {src}')

            if os.path.isfile(src):
                result.append(src)
                continue

            for root, dirs, files in os.walk(src):
                if '__pycache__' in root:
                    continue
                result += [
                    os.path.join(root, f)
                    for f in files
                    if not f.endswith('.pyc')
                ]
        self._listfiles = result
        return result

    async def __call__(self, target):
        await target.mkdir(self.dst)

        for path in await self.listfiles(target):
            if os.path.isdir(path):
                await target.mkdir(os.path.join(self.dst, path))
            elif '/' in path:
                dirname = os.path.join(
                    self.dst,
                    '/'.join(path.split('/')[:-1])
                )
                await target.mkdir(dirname)
                await target.copy(path, dirname)
            else:
                await target.copy(path, self.dst)

    def __str__(self):
        return f'Copy({", ".join(self.src)}, {self.dst})'

    async def cachekey(self, target):
        async def chksum(path):
            with open(path, 'rb') as f:
                return (path, str(binascii.crc32(f.read())))
        results = await asyncio.gather(
            *[chksum(f) for f in await self.listfiles(target)]
        )
        return {path: chks for path, chks in results}
