#!/usr/bin/env python3
"""Maker Script for releasing Docker images for this project.
"""

import argparse
from typing import Sequence

import make


def _project_has_invalid_version() -> list[str]:
    """Creates an error message if the project has no valid version."""
    return ["VERSION INVALID", "Version file must contain valid value"]


# region Push


def push(args: argparse.Namespace) -> int:
    """Pushes a Docker image for the project to the project‘s registry.

    Returns:
        Exit code.
    """
    # NOTE for `*["--quiet"] * (not args.debug),` (see below):
    # Do not try this at home: This is fun but too clever by half!
    # Inserts quiet option argument into command if debug is false, by unpacking
    # a list which either contains the option string (multiply by "true" aka 1)
    # or is empty (multiply by "false" aka 0).

    make.banner("RELEASE PUSH", "🎈")

    version = make.get_version(or_exit_using=_project_has_invalid_version)

    make.subprocess_run(
        [
            "docker",
            "tag",
            f"{args.build_name}-deploy:{version}",
            f"ghcr.io/edmw/{args.build_name}:{version}",
        ],
        verbose=args.verbose,
        debug=args.debug,
    )
    make.subprocess_run(
        [
            "docker",
            "push",
            *["--quiet"] * (not args.debug),  # see note above
            f"ghcr.io/edmw/{args.build_name}:{version}",
        ],
        verbose=True,
        debug=args.debug,
    )

    return 0


# endregion

# region main


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Release Helper -- provides project specific release workflows"
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
        "--name",
        help="base name for the build",
        dest="build_name",
        required=True,
    )
    parser.add_argument(
        "--debug",
        help="enable debug output",
        action="store_true",
    )
    parser.add_argument(
        "--insane",
        help="DANGER: disable all sanity checks",
        dest="check",
        action="store_false",
    )

    subparsers = parser.add_subparsers(title="workflows", required=True)

    parser_develop = subparsers.add_parser(
        "push",
        help="Execute workflow to push release",
    )
    parser_develop.set_defaults(func=push)

    args = parser.parse_args(argv)

    result = args.func(args)
    print()
    return result


if __name__ == "__main__":

    # get the ball rolling

    raise SystemExit(main())


# endregion
