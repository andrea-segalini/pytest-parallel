import pytest


@pytest.hookspec(firstresult=True)
def pytest_parallel_should_stop(session):
    """
    Return True to stop pytest-parallel workers from picking up new tests.

    This hook offers control over when other plugins (or `conftest.py`) can
    abort a parallel pytest session. It is called by each worker:

        - After every test finishes, and
        - Whenever a worker's test queue is idle.

    It uses `firstresult=True` semantics: the first registered implementation
    that returns a non-`None` value wins. Return `True` to stop, `False`
    to keep running, or `None` to defer to other implementations. If no
    implementation returns a non-`None` value, workers keep running as
    usual.

    This plugin does not register its own default implementation. This means
    that pytest's built-in `session.shouldstop` or `session.shouldfail` signals
    (set by features like `--maxfail`) are **not** observed across workers:
    each worker runs in its own subprocess with its own `session`, and there is
    currently no channel to propagate those signals from the master to the
    workers. Plugins that want cross-worker stop semantics must implement this
    hook themselves, typically by sharing state through `multiprocessing`
    primitives or files on disk.

    Each worker sees its own copy of `session`, so implementations should
    rely on state that is visible from within a worker process.
    """
