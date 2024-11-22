#!/usr/bin/env python3
"""Maker Script for building Docker images for this project.
"""

import argparse
import json
import subprocess
import sys
from collections import namedtuple
from typing import Any, Sequence

import check
import make


def _project_has_bad_git_branch(branchname: str) -> list[str]:
    """Creates an error message if the project is the wrong git branch."""
    return ["GIT: BAD BRANCH", f"Working branch must be {branchname}"]


def _project_has_outdated_git_branch() -> list[str]:
    """Creates an error message if the project has an outdated git branch."""
    return ["GIT: OUTDATED BRANCH", "Working branch must be up-to-date with upstream"]


def _project_has_dirty_git_status() -> list[str]:
    """Creates an error message if the project has a dirty git status."""
    return ["GIT: DIRTY STATUS", "Working tree must be clean"]


def _project_has_invalid_version() -> list[str]:
    """Creates an error message if the project has no valid version."""
    return ["VERSION INVALID", "Version file must contain valid value"]


def docker_inspect(image_name: str) -> dict[str, Any]:
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


def docker_build_command(platform: str, target: str, base_image: str, image_name: str) -> list[str]:
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


# A collection of values that are the results of building a Docker image.
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


def docker_build(
    platform: str,
    target: str,
    base_image: str,
    image_name: str,
    image_tag: str,
    verbose: bool = False,
    debug: bool = False,
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
    make.subprocess_run(
        command=docker_build_command(
            platform=platform, target=target, base_image=base_image, image_name=image_name
        ),
        environment={
            "DOCKER_BUILDKIT": "1",
            "DOCKER_CLI_HINTS": "false",
            "DOCKER_SCAN_SUGGEST": "false",
        },
        verbose=verbose,
        debug=debug,
    )
    try:
        image_info = docker_inspect(image_name=image_name)
        image_size = image_info["Size"]
        platform_os = image_info["Os"]
        platform_architecture = image_info["Architecture"]
        platform = f"{platform_os}/{platform_architecture}"
    except (ValueError, KeyError):
        make.banner("DOCKER:", "Unable to inspect image", fail=True)
        sys.exit(1)
    return BuildResult(
        target=target,
        image_tag=image_tag,
        image_name=image_name,
        image_size=image_size,
        platform=platform,
        base_image=base_image,
    )


def docker_build_result(result: BuildResult) -> None:
    """Prints the given build results collection."""
    make.banner(
        [
            "BUILD RESULT",
            f"Target: {result.target}",
            f"Image name: {result.image_name}",
            f"Image size: {make.sizeof_fmt(result.image_size)}",
            f"Platform: {result.platform}",
            f"Base image: {result.base_image}",
        ],
        char="=",
    )


def release(args: argparse.Namespace) -> int:
    """Builds the release version of this project.

    - Checks preconditions.
    - Bumps project‘s version.
    - Builds project‘s image for deployment.
    - Creates release tag in repository.

    Returns:
        Exit code.
    """
    make.banner("BUILD RELEASE", "👷")

    if args.check:
        check.git_branch_is("main", or_exit_using=_project_has_bad_git_branch)
        if check.git_branch_is_tracking("main"):
            check.git_branch_is_uptodate(or_exit_using=_project_has_outdated_git_branch)
        check.git_status_is_clean(or_exit_using=_project_has_dirty_git_status)

    version = make.get_version(or_exit_using=_project_has_invalid_version)
    match args.bump:
        case "minor":
            version = version.bump_minor()
        case "major":
            version = version.bump_major()
        case _:
            version = version.bump_patch()
    make.write_version(version)

    platform = args.platform
    base_image = args.base_image
    build_name = args.build_name
    build_target = "deploy"
    image_tag = str(version)
    build_result = docker_build(
        platform=platform,
        target=build_target,
        base_image=base_image,
        image_name=build_name,
        image_tag=image_tag,
        verbose=not args.quiet,
        debug=args.debug,
    )
    docker_build_result(build_result)

    make.subprocess_run(
        [
            "git",
            "commit",
            "VERSION",
            "--message",
            f"[make_build] build release version {build_result.image_name}",
        ],
        verbose=args.verbose,
        debug=args.debug,
    )

    make.subprocess_run(
        [
            "git",
            "tag",
            "--annotate",
            build_result.image_tag,
            "--message",
            f"[make_build] build release version {build_result.image_name}",
        ],
        verbose=args.verbose,
        debug=args.debug,
    )

    return 0


def build_develop(args: argparse.Namespace) -> int:
    """Builds the project‘s image for development."""
    make.banner("BUILD FOR DEVELOPMENT", "👷")

    platform = args.platform
    base_image = args.base_image
    build_name = args.build_name
    build_target = "develop"
    image_tag = "local"
    build_result = docker_build(
        platform=platform,
        target=build_target,
        base_image=base_image,
        image_name=build_name,
        image_tag=image_tag,
        verbose=not args.quiet,
        debug=args.debug,
    )
    docker_build_result(build_result)

    return 0


def build_deploy(args: argparse.Namespace) -> int:
    """Builds the project‘s image for deployment."""
    make.banner("BUILD FOR DEPLOYMENT", "👷")

    platform = args.platform
    base_image = args.base_image
    build_name = args.build_name
    build_target = "deploy"
    image_tag = "local"
    build_result = docker_build(
        platform=platform,
        target=build_target,
        base_image=base_image,
        image_name=build_name,
        image_tag=image_tag,
        verbose=not args.quiet,
        debug=args.debug,
    )
    docker_build_result(build_result)

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Helper -- provides project specific build workflows"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        help="decrease output verbosity",
        action="store_true",
    )
    parser.add_argument(
        "--platform",
        help="platform to build for",
        default="linux/amd64",
    )
    parser.add_argument(
        "--name",
        help="base name for the build",
        dest="build_name",
        required=True,
    )
    parser.add_argument(
        "--base",
        help="name of base image to build upon",
        dest="base_image",
        required=True,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="enable debug output",
        action="store_true",
    )
    parser.add_argument(
        "-x",
        "--insane",
        help="DANGER: disable all sanity checks",
        dest="check",
        action="store_false",
    )

    subparsers = parser.add_subparsers(title="workflows", required=True)

    parser_develop = subparsers.add_parser(
        "develop",
        help="Execute build workflow for developing this project",
    )
    parser_develop.set_defaults(func=build_develop)

    parser_deploy = subparsers.add_parser(
        "deploy",
        help="Execute build workflow for deploying this project",
    )
    parser_deploy.set_defaults(func=build_deploy)

    parser_release = subparsers.add_parser(
        "release",
        help="Execute build workflow for releasing this project",
    )
    parser_release.add_argument(
        "-b",
        "--bump",
        help="how to bump the version (default: patch)",
        choices=["patch", "minor", "major"],
        default="patch",
    )
    parser_release.set_defaults(func=release)

    args = parser.parse_args(argv)

    result = args.func(args)
    print()
    return result


if __name__ == "__main__":
    # get the ball rolling

    raise SystemExit(main())
