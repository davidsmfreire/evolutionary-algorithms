import pathlib
import nox


@nox.session(python=["3.9", "3.10.2"])
def test(session):
    session.run(
        "poetry",
        "export",
        "-f",
        "requirements.txt",
        "--output",
        "requirements.txt",
        "--dev",
        "--without-hashes",
        external=True,
    )

    session.install("-r", "requirements.txt")

    targets = ["format", "static-analysis", "security", "test", "build"]
    try:
        for target in targets:
            pip_specific_environment = {"RUN_COMMAND": ""}
            session.run(
                "make",
                target,
                env=pip_specific_environment,
                external=True,
            )
    finally:
        pathlib.Path("requirements.txt").unlink()
