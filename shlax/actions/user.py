import os
import re

from .packages import Packages


class User:
    def __init__(self, username, home, uid):
        self.username = username
        self.home = home
        self.uid = uid

    def __str__(self):
        return f'User({self.username}, {self.home}, {self.uid})'

    async def __call__(self, target):
        result = await target.rexec('id', self.uid)
        if result.rc == 0:
            old = re.match('.*\(([^)]*)\).*', result.out).group(1)
            await target.rexec(
                'usermod',
                '-d', self.home,
                '-l', self.username,
                old
            )
        else:
            await target.rexec(
                'useradd',
                '-d', self.home,
                '-u', self.uid,
                self.username
            )
