import sys
sys.path.insert(0, "./src")


# Avoid error return when no tests are collected
def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 5:
        session.exitstatus = 0