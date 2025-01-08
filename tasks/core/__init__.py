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
        """Wrapper for an invoke task that adds a `dry` parameter to the task.
        To be able to pass the value of the `dry` parameter to the wrapped task,
        the wrapper stores the value in the context's configuration dictionary
        and the wrapped task will be added as post task to the wrapper task.

        The wrapped task will keep all the configuration of the original task,
        especially the pre and post tasks.

        Before: pre-task -> task -> post-task
        After: wrapper -> wrapper-post-task = (pre-task -> task -> post-task)

        All arguments to the original task will be accepted and stored by the
        wrapper. When the wrapper‘s post-task is executed, the stored arguments
        will be passed to the wrapped original task.
        """

        def wrapper_with_arguments(*args: Any, **kwargs: Any) -> None:
            # Function for the wrapper task.
            # Store the arguments for the wrapped task in the context
            # configuration dictionary. Arguments are stored by function id of
            # the wrapped original task, so that other pre- and post-tasks will
            # get the correct arguments.
            context = args[0]
            if not hasattr(context.config, "simulation"):
                context.config.simulation = kwargs.pop("dry", False)
            if not hasattr(context.config, "_wrapper_kwargs_by_function"):
                context.config._wrapper_kwargs_by_function = {}
            context.config._wrapper_kwargs_by_function[str(id(task_function_to_wrap))] = kwargs

        def wrapped(context: Context, *args: Any, **kwargs: Any) -> T:
            # Function for the wrapped task.
            # Get the stored arguments for the wrapped task from the context
            # configuration dictionary and pass them to the wrapped original
            # task.
            wrapper_kwargs_by_function = context.config.get("_wrapper_kwargs_by_function", {})
            wrapper_kwargs = wrapper_kwargs_by_function.get(str(id(task_function_to_wrap)), *kwargs)
            return task_function_to_wrap(context, *args, **wrapper_kwargs)

        # Update the wrapper to look like the wrapped function.
        update_wrapper(wrapper_with_arguments, task_function_to_wrap)

        # Adjust the wrapper to behave like the wrapped function
        # and add the `dry` parameter.
        adjust_wrapper(wrapper_with_arguments, task_function_to_wrap)

        # Add the help text for the `dry` parameter.
        parameters_help = task_kwargs.get("help", {})
        parameters_help["dry"] = "Simulate the task without executing it."
        task_kwargs["help"] = parameters_help

        # Get and remove the pre- and post-tasks from the wrapper task
        # configuration to pass them to the wrapped task.
        task_pre = task_kwargs.pop("pre", None)
        task_post = task_kwargs.pop("post", None)

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
    """Decorator to print a banner before a task is executed.

    Adds a hint to the banner if the task is executed in simulation mode. For
    this to work, this decorator must be used after the `task` decorator.

    ````
    @task()
    @task_banner("🧹🧹🧹", "Cleaning")
    def clean(context: Context) -> None:
        ...
    ```
    """

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
    """Runs a command in the context of the given context.

    If the simulation mode is enabled, the command will not be executed, but
    the command string will be printed instead.

    Arguments:
        context: The context in which the command should be executed.
        command: The command to run.
        env: The environment variables to use for the command.

    Returns:
        The result of the command execution or `None` if the command was not
        executed.
    """

    simulation = context.config.get("simulation", False)

    command_string = " ".join(command)

    if simulation:
        Printer.simulation_would(["run command", Markup.info(command_string)])
        return None

    else:
        return context.run(command_string, env=env or {}, pty=True)
