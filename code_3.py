from __future__ import annotations

import sys
from io import StringIO
from typing import Callable, TextIO


def _run(main_wrapper: Callable[[TextIO, TextIO], None]) -> tuple[str, str, int]:
    """
    Wraps a callable `main_wrapper` with `StringIO` objects to capture standard
    output and error messages, and returns the captured outputs and the exit status
    of `main_wrapper`.

    Args:
        main_wrapper (Callable[[TextIO, TextIO], None]): main function that should
            be executed, and it is passed as a Callable object to the `run` function.

    Returns:
        tuple[str, str, int]: a tuple of the values of `stdout`, `stderr`, and the
        exit status of the main wrapped function.

    """
    stdout = StringIO()
    stderr = StringIO()

    try:
        main_wrapper(stdout, stderr)
        exit_status = 0
    except SystemExit as system_exit:
        assert isinstance(system_exit.code, int)
        exit_status = system_exit.code

    return stdout.getvalue(), stderr.getvalue(), exit_status


def run(args: list[str]) -> tuple[str, str, int]:
    # Lazy import to avoid needing to import all of mypy to call run_dmypy
    """
    Imports a module called `mypy.main` and uses it to call another function,
    `_run`, which takes a lambda function as input. The lambda function takes four
    arguments: `stdout`, `stderr`, `clean_exit`, and returns a tuple containing
    the output and exit code of the call to `main`.

    Args:
        args (list[str]): 1-3 command line arguments passed to the `run` function.

    Returns:
        tuple[str, str, int]: a tuple of the exit code, standard error message,
        and standard output message.

    """
    from mypy.main import main

    return _run(
        lambda stdout, stderr: main(args=args, stdout=stdout, stderr=stderr, clean_exit=True)
    )


def run_dmypy(args: list[str]) -> tuple[str, str, int]:
    """
    Takes a list of strings as input and runs the `main` function of the
    `mypy.dmypy.client` module, redirecting standard output and error to TextIO
    objects `stdout` and `stderr`.

    Args:
        args (list[str]): list of command-line arguments passed to the `main()`
            function of the dmypy client.

    Returns:
        tuple[str, str, int]: a tuple of two strings and an integer.

    """
    from mypy.dmypy.client import main

    # A bunch of effort has been put into threading stdout and stderr
    # through the main API to avoid the threadsafety problems of
    # modifying sys.stdout/sys.stderr, but that hasn't been done for
    # the dmypy client, so we just do the non-threadsafe thing.
    def f(stdout: TextIO, stderr: TextIO) -> None:
        """
        Modifies the standard streams `sys.stdout` and `sys.stderr` before executing
        `main`, then restores them after execution.

        Args:
            stdout (TextIO): text output stream and is used to replace the default
                output stream of the program with a new one.
            stderr (TextIO): 2nd output stream to which any errors or exceptions
                raised by the `main()` function will be printed.

        """
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = stdout
            sys.stderr = stderr
            main(args)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    return _run(f)
