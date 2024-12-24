import json
import subprocess
from collections import namedtuple
from typing import Any

from invoke.context import Context
from rich import print

from .bump import Bump
from .checker import Checker, CheckError
from .docker import DockerBase
from .mode import Mode
from .printer import Markup, Printer
from .project import CONFIGURATION, get_version, write_version
from .subprocess import run
from .utils import sizeof_fmt


class BuildError(Exception):
    def __init__(self, message: str, rich_message: str):
        super().__init__(message)
        self.rich_message = rich_message


BuildResult = namedtuple(
    "BuildResult",
    [
        "target",
        "image_tag",
        "image_name",
        "image_size",
        "platform",
        "base_image",
    ],
)


# region ⭐ Builder ⭐


class DockerBuilderError(Exception):
    def __init__(self, message: str, rich_message: str):
        super().__init__(message)
        self.rich_message = rich_message


class BuilderBase(DockerBase):
    def __init__(self, context: Context, platform: str, simulation: bool = False) -> None:
        super().__init__(context=context, simulation=simulation)
        self.platform = platform

    def docker_inspect(self, image_name: str) -> dict[str, Any]:
        """Returns Docker‘s information about the specified image."""
        result = subprocess.run(  # nosec
            ["docker", "inspect", image_name],
            check=True,
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            # Docker returns a list of results for every object to be inspected,
            # return the first and only one.
            return json.loads(result.stdout)[0]
        raise ValueError()

    def docker_build_command(
        self,
        platform: str,
        target: str,
        base_image: str,
        image_name: str,
    ) -> list[str]:
        """Returns the Docker command used to build the images for this project.

        Arguments:
            platform: The platform to build for.
            target: The target to be built, one of "develop" or "deploy".
            base_image: The name of the base image to build upon.
            image_name: The name and optionally the tag for the image to be built.

        Returns:
            List of command arguments.
        """
        return [
            "docker",
            "build",
            "--progress",
            "plain",
            "--target",
            target,
            "--file",
            "./Dockerfile",
            "--platform",
            platform,
            "--pull",
            "--build-arg",
            f"BASE_IMAGE={base_image}",
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            "--tag",
            image_name,
            ".",
        ]

    def docker_build(
        self,
        platform: str,
        target: str,
        base_image: str,
        image_name: str,
        image_tag: str,
        verbose: bool = False,
    ) -> BuildResult:
        """Build a Docker image for the project.

        Arguments:
            platform: The platform to build for.
            target: The target to be built, one of "develop" or "deploy".
            base_image: The name of the base image to build upon.
            image_name: The name to use for the resulting image.
            image_tag: The tag to append to the image name.
            verbose: If true, prints the output of the command.
                Defaults to False.
            debug: If true, prints debug information for the command.
                Defaults to False.

        Returns:
            A collection of values that are the results of building a the image.
        """
        image_name = f"{image_name}-{target}:{image_tag}"

        command = self.docker_build_command(
            platform=platform, target=target, base_image=base_image, image_name=image_name
        )
        environment = {
            "DOCKER_BUILDKIT": "1",
            "DOCKER_CLI_HINTS": "false",
            "DOCKER_SCAN_SUGGEST": "false",
        }
        if self.simulation:
            Printer.print_boxes(
                "SIMULATION", [("COMMAND", " ".join(command)), ("ENVIRONMENT", environment)]
            )

            return BuildResult(
                target=target,
                image_tag=image_tag,
                image_name=image_name,
                image_size=0,
                platform=platform,
                base_image=base_image,
            )

        run(  # nosec
            command=command,
            environment=environment,
            verbose=verbose,
        )

        try:
            image_info = self.docker_inspect(image_name=image_name)
            image_size = float(image_info["Size"])
            platform_os = image_info["Os"]
            platform_architecture = image_info["Architecture"]
            platform = f"{platform_os}/{platform_architecture}"
        except (ValueError, KeyError) as e:
            message = f"Inspecting image {Markup.ok(image_name, '"')}:\n  {Markup.not_ok(str(e))}"
            raise BuildError(Markup.plain(message), message) from e

        return BuildResult(
            target=target,
            image_tag=image_tag,
            image_name=image_name,
            image_size=image_size,
            platform=platform,
            base_image=base_image,
        )

    def build_develop(
        self,
        platform: str,
        base_image: str,
        build_name: str,
        quiet: bool = False,
    ) -> BuildResult:
        """Builds the project‘s image for development."""
        build_target = "develop"
        image_tag = "local"
        build_result = self.docker_build(
            platform=platform,
            target=build_target,
            base_image=base_image,
            image_name=build_name,
            image_tag=image_tag,
            verbose=not quiet,
        )
        return build_result

    def build_deploy(
        self,
        platform: str,
        base_image: str,
        build_name: str,
        quiet: bool = False,
    ) -> BuildResult:
        """Builds the project‘s image for deployment."""
        build_target = "deploy"
        image_tag = "local"
        build_result = self.docker_build(
            platform=platform,
            target=build_target,
            base_image=base_image,
            image_name=build_name,
            image_tag=image_tag,
            verbose=not quiet,
        )
        return build_result

    def build_release(
        self,
        bump: Bump,
        platform: str,
        base_image: str,
        build_name: str,
        verbose: bool = False,
        quiet: bool = False,
        do_check: bool = True,
    ) -> BuildResult:
        """Builds the release version of this project.

        - Checks preconditions.
        - Bumps project‘s version.
        - Builds project‘s image for deployment.
        - Creates release tag in repository.

        Returns:
            Exit code.
        """
        if do_check:
            checker = Checker(simulation=self.simulation)
            checker.git_branch_is("main")
            if checker.git_branch_is_tracking("main"):
                checker.git_branch_is_uptodate()
            checker.git_status_is_clean()

        try:
            version = get_version()
        except (FileNotFoundError, ValueError) as e:
            message = "Error reading project version"
            raise BuildError(Markup.plain(message), message) from e

        match bump:
            case Bump.PATCH:
                version = version.bump_patch()
            case Bump.MINOR:
                version = version.bump_minor()
            case Bump.MAJOR:
                version = version.bump_major()

        if self.simulation:
            print(f"SIMULATION: Would write {Markup.info(str(version))} to version file")
        else:
            write_version(version)

        platform = platform
        base_image = base_image
        build_name = build_name
        build_target = "deploy"
        image_tag = str(version)
        build_result = self.docker_build(
            platform=platform,
            target=build_target,
            base_image=base_image,
            image_name=build_name,
            image_tag=image_tag,
            verbose=not quiet,
        )

        if self.simulation:
            print("SIMULATION: Would commit version file")
        else:
            run(  # nosec
                [
                    "git",
                    "commit",
                    "VERSION",
                    "--message",
                    f"[make_build] build release version {build_result.image_name}",
                ],
                verbose=verbose,
            )

        if self.simulation:
            print(f"SIMULATION: Would create tag for {Markup.info(build_result.image_tag)}")
        else:
            run(  # nosec
                [
                    "git",
                    "tag",
                    "--annotate",
                    build_result.image_tag,
                    "--message",
                    f"[make_build] build release version {build_result.image_name}",
                ],
                verbose=verbose,
            )

        return build_result

    def print_build_result(self, build_result: dict[str, str]) -> None:
        data = [
            ("Target", build_result["target"]),
            ("Image name", build_result["image_name"]),
            ("Image size", sizeof_fmt(float(build_result["image_size"]))),
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
                case Mode.PRODUCTION:
                    message = "Building Webapp for Production"
            self.print_banner("👷👷👷", message)

            try:
                if mode in [Mode.DEVELOP, Mode.DEVELOP_DEBUG]:
                    build_result = self.build_develop(
                        platform=self.platform,
                        base_image=CONFIGURATION.base_image_name,
                        build_name=CONFIGURATION.build_image_name,
                    )
                elif mode == Mode.PRODUCTION:
                    build_result = self.build_deploy(
                        platform=self.platform,
                        base_image=CONFIGURATION.base_image_name,
                        build_name=CONFIGURATION.build_image_name,
                    )
                else:
                    raise ValueError(f"Invalid mode: {mode}")

                self.print_build_result(build_result._asdict())

            except BuildError as e:
                message = (
                    f"Error while building image for development in mode {Markup.mode(mode)}:\n\n"
                    + e.rich_message
                )
                raise DockerBuilderError(Markup.plain(message), message) from e

    # endregion Development

    # region Release

    class Release(BuilderBase):

        def build(self, bump: Bump) -> None:
            self.print_banner("👷👷👷", "Building Webapp for Release")

            try:
                build_result = self.build_release(
                    bump=bump,
                    platform=self.platform,
                    base_image=CONFIGURATION.base_image_name,
                    build_name=CONFIGURATION.build_image_name,
                    do_check=True,
                )
                self.print_build_result(build_result._asdict())

            except (CheckError, BuildError) as e:
                message = f"Error while building image for release:\n\n{e.rich_message}"
                raise DockerBuilderError(Markup.plain(message), message) from e

    # endregion Release


# endregion ⭐ Builder ⭐
