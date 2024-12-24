from .docker import DockerBase
from .printer import Markup
from .project import CONFIGURATION, get_version


class PushError(Exception):
    def __init__(self, message: str, rich_message: str):
        super().__init__(message)
        self.rich_message = rich_message


# region ⭐ Pusher ⭐


class PusherBase(DockerBase):
    pass


class DockerPusher:

    # region Application

    class Application(PusherBase):

        def build_tag_command(self, version: str, build_name: str) -> list[str]:
            return [
                "docker",
                "tag",
                f"{build_name}-deploy:{version}",
                f"ghcr.io/edmw/{build_name}:{version}",
            ]

        def build_push_command(self, version: str, build_name: str) -> list[str]:
            return [
                "docker",
                "push",
                # *["--quiet"] * (not args.debug),
                f"ghcr.io/edmw/{build_name}:{version}",
            ]

        def push(self) -> None:
            self.print_banner("🎈🎈🎈", "Pushing Webapp to Package Repository")

            try:
                version = get_version()
            except (FileNotFoundError, ValueError) as e:
                message = "Error reading project version"
                raise PushError(Markup.plain(message), message) from e

            command = self.build_tag_command(
                version=str(version), build_name=CONFIGURATION.build_image_name
            )
            self.run_in_context(command)

            command = self.build_push_command(
                version=str(version), build_name=CONFIGURATION.build_image_name
            )
            self.run_in_context(command)

    # endregion Application


# endregion ⭐ Runner ⭐
