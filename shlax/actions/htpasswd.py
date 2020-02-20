import hashlib
import secrets
import string

from .base import Action


class Htpasswd(Action):
    """Ensure a user is present in an htpasswd file."""
    display_variables = ('user', 'path')
    regexps = {
        r'(.*)': '{red}\\1{gray}:${blue}\\2${blue}',
        r'([^:]*):\\$([^$]*)\\$(.*)$': '{red}\\1{gray}:${blue}\\2${blue}\\3',
    }

    def __init__(self, user, path, **kwargs):
        self.user = user
        self.path = path
        super().__init__(**kwargs)

    async def apply(self):
        found = False
        htpasswd = await self.target.exec(
            'cat', self.path, raises=False)
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
            await self.target.exec(f'echo {line} >> {self.path}')
