from __future__ import annotations

import sys
from io import StringIO
from typing import Callable, TextIO


def _run(main_wrapper: Callable[[TextIO, TextIO], None]) -> tuple[str, str, int]:
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
    from mypy.main import main

    return _run(
        lambda stdout, stderr: main(args=args, stdout=stdout, stderr=stderr, clean_exit=True)
    )


def run_dmypy(args: list[str]) -> tuple[str, str, int]:
    from mypy.dmypy.client import main

    # A bunch of effort has been put into threading stdout and stderr
    # through the main API to avoid the threadsafety problems of
    # modifying sys.stdout/sys.stderr, but that hasn't been done for
    # the dmypy client, so we just do the non-threadsafe thing.
    def f(stdout: TextIO, stderr: TextIO) -> None:
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
