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
        ),
        apt=dict(
            update='apt-get -y update',
            upgrade='apt-get -y upgrade',
            install='apt-get -y --no-install-recommends install',
        ),
        pacman=dict(
            update='pacman -Sy',
            upgrade='pacman -Su --noconfirm',
            install='pacman -S --noconfirm',
        ),
        dnf=dict(
            update='dnf makecache --assumeyes',
            upgrade='dnf upgrade --best --assumeyes --skip-broken',  # noqa
            install='dnf install --setopt=install_weak_deps=False --best --assumeyes',  # noqa
        ),
        yum=dict(
            update='yum update',
            upgrade='yum upgrade',
            install='yum install',
        ),
    )

    installed = []

    def __init__(self, *packages, upgrade=True):
        self.packages = []
        self.upgrade = upgrade
        for package in packages:
            line = dedent(package).strip().replace('\n', ' ')
            self.packages += line.split(' ')

    @property
    def cache_root(self):
        if 'CACHE_DIR' in os.environ:
            return os.path.join(os.getenv('CACHE_DIR'))
        else:
            return os.path.join(os.getenv('HOME'), '.cache')

    async def update(self, target):
        # run pkgmgr_setup functions ie. apk_setup
        cachedir = await getattr(self, self.mgr + '_setup')(target)

        lastupdate = None
        if os.path.exists(cachedir + '/lastupdate'):
            with open(cachedir + '/lastupdate', 'r') as f:
                try:
                    lastupdate = int(f.read().strip())
                except:
                    pass

        if not os.path.exists(cachedir):
            os.makedirs(cachedir)

        now = int(datetime.now().strftime('%s'))
        # cache for a week
        if not lastupdate or now - lastupdate > 604800:
            # crude lockfile implementation, should work against *most*
            # race-conditions ...
            lockfile = cachedir + '/update.lock'
            if not os.path.exists(lockfile):
                with open(lockfile, 'w+') as f:
                    f.write(str(os.getpid()))

                try:
                    await target.rexec(self.cmds['update'])
                finally:
                    os.unlink(lockfile)

                with open(cachedir + '/lastupdate', 'w+') as f:
                    f.write(str(now))
            else:
                while os.path.exists(lockfile):
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
        codename = (await self.rexec(
            f'source {self.mnt}/etc/os-release; echo $VERSION_CODENAME'
        )).out
        cachedir = os.path.join(self.cache_root, self.mgr, codename)
        await self.rexec('rm /etc/apt/apt.conf.d/docker-clean')
        cache_archives = os.path.join(cachedir, 'archives')
        await self.mount(cache_archives, f'/var/cache/apt/archives')
        cache_lists = os.path.join(cachedir, 'lists')
        await self.mount(cache_lists, f'/var/lib/apt/lists')
        return cachedir

    async def pacman_setup(self, target):
        return self.cache_root + '/pacman'

    def __str__(self):
        return f'Packages({self.packages}, upgrade={self.upgrade})'
