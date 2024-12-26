from ast import Call
from collections.abc import Callable
from functools import update_wrapper, wraps
from inspect import Parameter, signature
from typing import Any, TypeVar

from invoke.context import Context
from invoke.runners import Result
from invoke.tasks import task as invoke_task

from .printer import Markup, Printer

T = TypeVar("T")

V = TypeVar("V")


def task(*task_args: Any, **task_kwargs: Any) -> Callable:
    """Marks wrapped callable object as a valid Invoke task.

    This decorator is a wrapper around Invoke's `invoke.tasks.task` decorator.
    It adds a `dry` parameter to the wrapped callable object, which allows
    simulating the task without executing it.

    The value of the dry parameter is set to `False` by default. It can be set
    to `True` by passing `dry=True` to the task function. The value will be
    stored in the context's configuration dictionary under the key `simulation`.

    It can be accessed using `context.config.get("simulation", False)`.
    """

    def adjust_wrapper(wrapper: Callable, wrapped: Callable) -> None:
        """Adjusts the signature of the wrapper function to match the signature
        of the wrapped callable and extends the signature with the dry
        parameter.
        """
        wrapped_signature = signature(wrapped)
        wrapped_parameters = list(wrapped_signature.parameters.values())
        wrapped_parameters.append(
            Parameter(
                "dry",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=False,
                annotation=bool,
            )
        )
        wrapper.__setattr__("__signature__", wrapped_signature.replace(parameters=wrapped_parameters))

    def wrapper(task_function_to_wrap: Callable[..., T]) -> Callable:
        def wrapped(context: Context, *args: Any, **kwargs: Any) -> T:
            wrapper_kwargs = context.config._get("wrapper_kwargs", *kwargs)
            return task_function_to_wrap(context, *args, **wrapper_kwargs)

        def wrapper_with_arguments(*args: Any, **kwargs: Any) -> None:
            context = args[0]
            if not hasattr(context.config, "simulation"):
                context.config.simulation = kwargs.pop("dry", False)
            context.config.wrapper_kwargs = kwargs

        # Updates the wrapper to look like the wrapped function.
        update_wrapper(wrapper_with_arguments, task_function_to_wrap)
        # Adjust the wrapper to behave like the wrapped function.
        adjust_wrapper(wrapper_with_arguments, task_function_to_wrap)

        task_pre = task_kwargs.pop("pre", None)
        task_post = task_kwargs.pop("post", None)

        parameters_help = task_kwargs.get("help", {})
        parameters_help["dry"] = "Simulate the task without executing it."
        task_kwargs["help"] = parameters_help

        wrapper_task = invoke_task(
            wrapper_with_arguments,
            *task_args,
            post=[
                invoke_task(
                    wrapped,
                    # Name of wrapped tasked must be unique to avoid deduplication.
                    name=f"{repr(task_function_to_wrap)}",
                    pre=task_pre,
                    post=task_post,
                )
            ],
            pre=None,
            **task_kwargs,
        )
        return wrapper_task

    return wrapper


def task_banner(title: str, message: str) -> Callable:

    def decorator(function: Callable[..., T]) -> Callable[..., T]:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            context = args[0]
            simulation = context.config.get("simulation", False)

            m = message
            if simulation:
                m += f"\n{Markup.info('SIMULATION', ')')}"
            Printer.print_banner(title, m)

            return function(*args, **kwargs)

        return wrapper

    return decorator


def run_in_context(context: Context, command: list[str], env: dict | None = None) -> Result | None:
    simulation = context.config.get("simulation", False)

    command_string = " ".join(command)
    if simulation:
        Printer.simulation_would(["run command", Markup.info(command_string)])
    else:
        context.run(command_string, env=env or {}, pty=True)
