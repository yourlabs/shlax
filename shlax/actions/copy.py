import asyncio
import binascii
import os


class Copy:
    def __init__(self, *args):
        self.src = args[:-1]
        self.dst = args[-1]

    def listfiles(self):
        if getattr(self, '_listfiles', None):
            return self._listfiles

        result = []
        for src in self.src:
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

        for path in self.listfiles():
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

    async def cachekey(self):
        async def chksum(path):
            with open(path, 'rb') as f:
                return (path, str(binascii.crc32(f.read())))
        results = await asyncio.gather(*[chksum(f) for f in self.listfiles()])
        return {path: chks for path, chks in results}
