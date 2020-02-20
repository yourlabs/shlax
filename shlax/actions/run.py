from .base import Action


class Run(Action):
    """Run a script or command on a target."""
    async def call(self, *args, **kwargs):
        image = self.kwargs.get('image', None)
        if not image:
            return await self.exec(*self.args, **self.kwargs)
        from ..targets.buildah import Buildah
        from ..targets.docker import Docker
        if isinstance(image, Buildah):
            breakpoint()
            result = await self.action(image, *args, **kwargs)

        return await Docker(
            image=image,
        ).exec(*args, **kwargs)
