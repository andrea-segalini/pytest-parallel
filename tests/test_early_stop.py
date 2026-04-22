"""
Tests covering pytest-parallel"s master-side early-stop behaviour.

The plugin observes the master session"s `shouldstop` and `shouldfail` flags
after each worker test report is dispatched. When either flag is set (for
example because `--maxfail` has been tripped) the plugin drains the shared test
queue so that idle workers exit via their existing "stop" sentinel. Tests
already running in a worker are allowed to finish, matching pytest"s normal
`--maxfail` semantics.
"""

import pytest


def _create_test_module_content(num_tests, tests_pass=False):
    """
    Create the contents of a test module where every test either passes or
    fails after a short sleep.

    The sleep is important: it makes the scheduling deterministic enough that
    workers cannot race through the entire backlog before the master has a
    chance to dispatch a log report and drain the queue.

    :param num_tests: The number of tests to create.
    :param tests_pass: Whether the tests should pass or fail.
    :return: The contents of a test module.
    """
    test_functions = "\n\n".join(
        f"def test_{i}():\n    time.sleep(0.05)\n    assert {tests_pass}"
        for i in range(num_tests)
    )
    return f"""
import time

{test_functions}
"""


@pytest.mark.parametrize(
    "cli_args",
    [
        ["--workers=2"],
        ["--tests-per-worker=2"],
        ["--workers=2", "--tests-per-worker=2"],
    ],
)
def test_maxfail_stops_before_entire_backlog_runs(testdir, cli_args):
    """
    Test that with --maxfail=1 and many pending tests, the backlog must not
    all run.

    The precise number that does run is nondeterministic (it depends on how
    many workers/threads were concurrently past `queue.get()` at the moment
    the master drained the queue). This test only asserts the important
    invariant: fewer than the full backlog ran.
    """
    num_tests = 20
    testdir.makepyfile(_create_test_module_content(num_tests))
    result = testdir.runpytest("--maxfail=1", *cli_args)

    # Failed exit code expected because at least one test failed.
    assert result.ret == 1

    outcomes = result.parseoutcomes()
    failed = outcomes.get("failed", 0)
    passed = outcomes.get("passed", 0)

    # At least one test ran and failed (that"s what tripped --maxfail).
    assert failed >= 1
    # But the drain must have prevented the full backlog from executing.
    assert failed + passed < num_tests, (
        f"Expected early stop to drop some pending tests, but "
        f"{failed + passed} of {num_tests} ran ({cli_args=})"
    )


@pytest.mark.parametrize(
    "cli_args",
    [
        ["--workers=2"],
        ["--tests-per-worker=2"],
        ["--workers=2", "--tests-per-worker=2"],
    ],
)
def test_no_maxfail_runs_entire_backlog(testdir, cli_args):
    """
    Test that without `--maxfail`, the drain must not fire. Every failing test
    in the queue must still be executed.
    """
    num_tests = 20
    testdir.makepyfile(_create_test_module_content(num_tests))
    result = testdir.runpytest(*cli_args)

    assert result.ret == 1
    result.assert_outcomes(failed=num_tests)


@pytest.mark.parametrize(
    "cli_args",
    [
        ["--workers=2"],
        ["--tests-per-worker=2"],
        ["--workers=2", "--tests-per-worker=2"],
    ],
)
def test_maxfail_not_tripped_when_all_pass(testdir, cli_args):
    """
    Test that passing tests do not trip any stop flag.
    """
    num_tests = 20
    testdir.makepyfile(_create_test_module_content(num_tests, tests_pass=True))
    result = testdir.runpytest("--maxfail=1", *cli_args)

    assert result.ret == 0
    result.assert_outcomes(passed=num_tests)
