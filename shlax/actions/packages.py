import asyncio
import copy

from datetime import datetime
from glob import glob
import os
import subprocess
from textwrap import dedent


class Packages:
    """
    Package manager abstract layer with caching.

    It's a central piece of the build process, and does iterate over other
    container visitors in order to pick up packages. For example, the Pip
    visitor will declare ``self.packages = dict(apt=['python3-pip'])``, and the
    Packages visitor will pick it up.
    """
    regexps = {
        #r'Installing ([\w\d-]+)': '{cyan}\\1',
        r'Installing': '{cyan}lol',
    }

    mgrs = dict(
        apk=dict(
            update='apk update',
            upgrade='apk upgrade',
            install='apk add',
            host=None,
        ),
        apt=dict(
            update='apt-get -y update',
            upgrade='apt-get -y upgrade',
            install='apt-get -y --no-install-recommends install',
            host=None,
        ),
        pacman=dict(
            update='pacman -Sy',
            upgrade='pacman -Su --noconfirm',
            install='pacman -S --noconfirm',
            lastupdate='stat -c %Y /var/lib/pacman/sync/core.db',
            host='/var/lib/pacman',
        ),
        dnf=dict(
            update='dnf makecache --assumeyes',
            upgrade='dnf upgrade --best --assumeyes --skip-broken',  # noqa
            install='dnf install --setopt=install_weak_deps=False --best --assumeyes',  # noqa
            lastupdate='stat -c %Y /var/cache/dnf/* | head -n1',
            host=None,
        ),
        yum=dict(
            update='yum update',
            upgrade='yum upgrade',
            install='yum install',
            host=None,
        ),
    )

    installed = []

    def __init__(self, *packages, upgrade=False):
        self.packages = []
        self.upgrade = upgrade
        for package in packages:
            line = dedent(package).strip().replace('\n', ' ')
            self.packages += line.split(' ')

    async def cache_setup(self, target):
        # Try to use the host cache directory if present rather than home
        # directory, in cases where host and guest are the same distros
        hostpath = self.mgrs[self.mgr]['host']
        if target.exists(hostpath):
            self.cache_root = hostpath

        if 'CACHE_DIR' in os.environ:
            self.cache_root = os.path.join(os.getenv('CACHE_DIR'))
        else:
            self.cache_root = os.path.join(await target.parent.getenv('HOME'), '.cache')

        # run pkgmgr_setup functions ie. apk_setup
        await getattr(self, self.mgr + '_setup')(target)

    async def update(self, target):
        # lastupdate = await target.exec(self.cmds['lastupdate'], raises=False)
        # lastupdate = int(lastupdate.out) if lastupdate.rc == 0 else None
        lastupdate = None
        now = int(datetime.now().strftime('%s'))
        if not lastupdate or now - lastupdate > 604800:
            await target.rexec(self.cmds['update'])

        return

        # disabling with the above return call until needed again
        # might have to rewrite this to not have our own lockfile
        # or find a better place on the filesystem
        # also make sure the lockfile is actually needed when running on
        # targets that don't have isguest=True
        if not lastupdate or now - lastupdate > 604800:
            # crude lockfile implementation, should work against *most*
            # race-conditions ...
            lockfile = cachedir + '/update.lock'
            if not await target.parent.exists(lockfile):
                await target.parent.write(lockfile, str(os.getpid()))

                try:
                    await target.rexec(self.cmds['update'])
                finally:
                    await target.parent.rm(lockfile)

                await target.parent.write(cachedir + '/lastupdate', str(now))
            else:
                while await target.parent.exists(lockfile):
                    print(f'{self.target} | Waiting for {lockfile} ...')
                    await asyncio.sleep(1)

    async def __call__(self, target):
        cached = getattr(target, 'pkgmgr', None)
        if cached:
            self.mgr = cached
        else:
            mgr = await target.which(*self.mgrs.keys())
            if mgr:
                self.mgr = mgr[0].split('/')[-1]

        if not self.mgr:
            raise Exception('Packages does not yet support this distro')

        self.cmds = self.mgrs[self.mgr]

        if target.isguest:
            # we're going to mount
            await self.cache_setup(target)

        await self.update(target)

        if self.upgrade:
            await target.rexec(self.cmds['upgrade'])

        packages = []
        for package in self.packages:
            if ',' in package:
                parts = package.split(',')
                package = parts[0]
                if self.mgr in parts[1:]:
                    # include apt on apt
                    packages.append(package)
            else:
                packages.append(package)

        await target.rexec(*self.cmds['install'].split(' ') + packages)

    async def apk_setup(self, target):
        cachedir = os.path.join(self.cache_root, self.mgr)
        await target.mount(cachedir, '/var/cache/apk')
        # special step to enable apk cache
        await target.rexec('ln -sf /var/cache/apk /etc/apk/cache')
        return cachedir

    async def dnf_setup(self, target):
        cachedir = os.path.join(self.cache_root, self.mgr)
        await target.mount(cachedir, f'/var/cache/{self.mgr}')
        await target.rexec('echo keepcache=True >> /etc/dnf/dnf.conf')
        return cachedir

    async def apt_setup(self, target):
        codename = (await target.rexec(
            f'source /etc/os-release; echo $VERSION_CODENAME'
        )).out
        cachedir = os.path.join(self.cache_root, self.mgr, codename)
        await self.rexec('rm /etc/apt/apt.conf.d/docker-clean')
        cache_archives = os.path.join(cachedir, 'archives')
        await target.mount(cache_archives, f'/var/cache/apt/archives')
        cache_lists = os.path.join(cachedir, 'lists')
        await target.mount(cache_lists, f'/var/lib/apt/lists')
        return cachedir

    async def pacman_setup(self, target):
        cachedir = os.path.join(self.cache_root, self.mgr)
        await target.mkdir(cachedir + '/cache', cachedir + '/sync')
        await target.mount(cachedir + '/sync', '/var/lib/pacman/sync')
        await target.mount(cachedir + '/cache', '/var/cache/pacman')
        if await target.host.exists('/etc/pacman.d/mirrorlist'):
            await target.copy('/etc/pacman.d/mirrorlist', '/etc/pacman.d/mirrorlist')

    def __str__(self):
        return f'Packages({self.packages}, upgrade={self.upgrade})'
