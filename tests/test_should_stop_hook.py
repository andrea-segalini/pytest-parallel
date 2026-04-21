def test_custom_should_stop_hook_halts_workers(testdir):
    """
    Test that a registered implementation of `pytest_parallel_should_stop`
    that returns `True` causes the workers to stop before running every test.

    The conftest writes a sentinel file after the first test completes and
    then returns True from the hook; remaining tests must not run.
    """
    testdir.makepyfile(conftest="""
        import os

        SENTINEL = os.path.join(os.path.dirname(__file__), 'stop.sentinel')

        def pytest_runtest_logreport(report):
            if report.when == 'call':
                open(SENTINEL, 'a').close()

        def pytest_parallel_should_stop(session):
            return os.path.exists(SENTINEL)
    """)
    testdir.makepyfile("""
        def test_1(): pass
        def test_2(): pass
        def test_3(): pass
        def test_4(): pass
        def test_5(): pass
    """)
    result = testdir.runpytest('--workers=1')
    result.assert_outcomes(passed=1)
    assert result.ret == 0


def test_should_stop_hook_false_keeps_running(testdir):
    """
    Test that an implementation that always returns `False` must not interfere
    with a normal run; every test should still execute.
    """
    testdir.makepyfile(conftest="""
        def pytest_parallel_should_stop(session):
            return False
    """)
    testdir.makepyfile("""
        def test_1(): pass
        def test_2(): pass
        def test_3(): pass
    """)
    result = testdir.runpytest('--workers=1')
    result.assert_outcomes(passed=3)
    assert result.ret == 0


def test_should_stop_hook_none_is_neutral(testdir):
    """
    Test that returning `None` from an implementation is neutral: it does not
    stop the workers, and it does not itself cause a failure. With no other
    implementation registered, workers run every collected test to completion.
    """
    testdir.makepyfile(conftest="""
        def pytest_parallel_should_stop(session):
            return None
    """)
    testdir.makepyfile("""
        def test_1(): pass
        def test_2(): pass
        def test_3(): pass
    """)
    result = testdir.runpytest('--workers=1')
    result.assert_outcomes(passed=3)
    assert result.ret == 0
