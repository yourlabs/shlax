import hashlib
import secrets
import string

from .base import Action


class Htpasswd(Action):
    def __init__(self, path, user, *args, **kwargs):
        self.path = path
        self.user = user
        super().__init__(*args, **kwargs)

    async def call(self, *args, **kwargs):
        found = False
        htpasswd = await self.exec('cat', self.path, raises=False)
        if htpasswd.rc == 0:
            for line in htpasswd.out.split('\n'):
                if line.startswith(self.user + ':'):
                    found = True
                    break

        if not found:
            self.password = ''.join(secrets.choice(
                string.ascii_letters + string.digits
            ) for i in range(20))
            hashed = hashlib.sha1(self.password.encode('utf8'))
            line = f'{self.user}:\\$sha1\\${hashed.hexdigest()}'
            await self.exec(f'echo {line} >> {self.path}')
