from invoke.context import Context

from .bump import Bump
from .mode import Mode
from .printer import Printer
from .project import CONFIGURATION
from .scripts import make, make_build

# region ⭐ Builder ⭐


class BuilderBase:
    def __init__(self, context: Context, platform: str) -> None:
        self.context = context

        self.platform = platform

    def print_build_result(self, build_result: dict[str, str]) -> None:
        data = [
            ("Target", build_result["target"]),
            ("Image name", build_result["image_name"]),
            ("Image size", make.sizeof_fmt(build_result["image_size"])),
            ("Platform", build_result["platform"]),
            ("Base image", build_result["base_image"]),
        ]
        Printer.print_table("👷 BUILD RESULT 👷", data)


class DockerBuilder:

    # region Development

    class Development(BuilderBase):

        def build(self, mode: Mode = Mode.DEVELOP) -> None:
            match mode:
                case Mode.DEVELOP | Mode.DEVELOP_DEBUG:
                    message = "Building Webapp for Development"
                case Mode.DEPLOY:
                    message = "Building Webapp for Deployment"
            Printer.print_banner("👷👷👷", message)

            if mode in [Mode.DEVELOP, Mode.DEVELOP_DEBUG]:
                build_result = make_build.build_develop(
                    platform=self.platform,
                    base_image=CONFIGURATION.base_image_name,
                    build_name=CONFIGURATION.build_image_name,
                    output=False,
                )
            elif mode == Mode.DEPLOY:
                build_result = make_build.build_deploy(
                    platform=self.platform,
                    base_image=CONFIGURATION.base_image_name,
                    build_name=CONFIGURATION.build_image_name,
                    output=False,
                )
            else:
                raise ValueError(f"Invalid mode: {mode}")

            self.print_build_result(build_result._asdict())

    # endregion Development

    # region Release

    class Release(BuilderBase):

        def build(self, bump: Bump) -> None:
            message = "Building Webapp for Release"
            Printer.print_banner("👷👷👷", message)

            build_result = make_build.release(
                bump=str(bump),
                platform=self.platform,
                base_image=CONFIGURATION.base_image_name,
                build_name=CONFIGURATION.build_image_name,
                do_check=True,
            )

            self.print_build_result(build_result._asdict())

    # endregion Release


# endregion ⭐ Builder ⭐
