from .base import Action


class Run(Action):
    """Run a script or command on a target."""
    def __init__(self, *args, image=None, **kwargs):
        super().__init__(**kwargs)
        self.args = args
        self.kwargs = kwargs
        self.image = image

    async def apply(self):
        if not self.image:
            return await self.target.exec(*self.args, **self.kwargs)

        from ..targets.buildah import Buildah
        from ..targets.docker import Docker

        if isinstance(image, Buildah):
            result = await self.action(image, *args, **kwargs)

        return await Docker(
            image=image,
        ).exec(*args, **kwargs)
