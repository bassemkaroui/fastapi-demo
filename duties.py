from __future__ import annotations

import os
import shutil
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from duty import duty, tools

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from duty.collection import Duty
    from duty.context import Context

PY_SRC_PATHS = (Path(_) for _ in ("src", "tests", "duties.py"))
PY_SRC_LIST = tuple(str(_) for _ in PY_SRC_PATHS)
CI = os.environ.get("CI", "0") in {"1", "true", "yes", ""}
WINDOWS = os.name == "nt"
PTY = not WINDOWS and not CI


# -----------------------------------------------------------------------------
# Helper functions ------------------------------------------------------------
# -----------------------------------------------------------------------------


def _is_running_in_docker() -> bool:
    """Check if the code is running inside a Docker container."""
    return Path("/.dockerenv").exists()


def _verify_uv_installed(ctx: Context, duty_name: str) -> None:
    """Ensure that the `uv` is installed, attempting installation if missing."""
    if not shutil.which("uv"):
        ctx.run("false", title="⚡ uv was not found", nofail=True)
        if shutil.which("curl"):
            ctx.run(
                "curl -LsSf https://astral.sh/uv/install.sh | sh",
                title="Installing uv with curl",
                allow_overrides=False,
            )
        elif shutil.which("wget"):
            ctx.run(
                "wget -qO- https://astral.sh/uv/install.sh | sh",
                title="Installing uv with wget",
                allow_overrides=False,
            )
        else:
            raise ValueError(
                f"make: {duty_name.replace('_', '-')}: uv must be installed, "
                "see https://docs.astral.sh/uv/getting-started/installation/"
            )


def _pick_env(ctx: Context, env: str = "dev", action: str = "start") -> str:
    while True:
        ctx.run(
            "true",
            title=f"Pick the environment you want to {action} ([dev]/prod): ",
            nofail=True,
            allow_overrides=False,
        )
        env = input().strip().lower()
        if not env:
            return "dev"
        if env in ("dev", "prod"):
            return env


def _ask_user_confirmation(prompt: str) -> bool:
    """Prompt the user for a yes/no confirmation"""
    while True:
        # write & flush so the user actually sees the question
        sys.stdout.write(prompt)
        sys.stdout.flush()
        line = sys.stdin.readline()
        # EOF or empty line → treat as "no"
        if not line:
            return False

        response = line.strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False


def _is_interactive() -> bool:
    """Check if the current session is interactive (i.e., not running in CI)"""
    return sys.stdin.isatty() and os.environ.get("CI", "").lower() != "true"


@contextmanager
def _setup_container(ctx: Context) -> Iterator[None]:
    """Ensure the dev Docker container is running for the duration of a context block.

    Starts the developement Docker containers if they are not already running.
    At the end of the context, optionally prompts the user to stop and remove the containers,
    but only if the session is interactive.
    """
    build_docker_images = (
        _ask_user_confirmation("Do you want to build the dev containers first (y/n): ")
        if _is_interactive()
        else False
    )
    if build_docker_images:
        docker_build.run(env="dev")
        docker_start.run(env="dev")
    else:
        output = ctx.run(
            ["docker", "compose", "top"], silent=True, allow_overrides=False, capture=True
        )
        if "fastapi-demo-dev" not in output:
            docker_start.run(env="dev")
    try:
        yield
    finally:
        if _is_interactive() and _ask_user_confirmation(
            "Do you want to stop and remove the containers (y/n): "
        ):
            docker_stop.run(env="dev")


def dockerized_duty(*args: str, **kwargs: Any) -> Callable[[Duty], Duty]:
    """Decorator to create a Dockerized version of a given duty.

    Wraps a duty function so that it runs inside the `fastapi-demo-dev` container
    using `docker compose exec`.
    Automatically ensures the container is running before execution,
    and optionally passes CLI arguments and keyword arguments to the duty.

    Args:
        *args: Positional arguments to pass to the duty.
        **kwargs: Keyword arguments to pass to the duty.

    Returns:
        The original duty, unchanged, while registering a Dockerized version.
    """

    def wrap_duty_for_docker_exec(duty_instance: Duty) -> Duty:
        new_name = "docker_exec_" + duty_instance.name.replace("-", "_")
        args_str = " ".join(args)
        kwargs_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
        cmd = ["docker", "compose", "exec", "fastapi-demo-dev", "duty", duty_instance.name]
        if args_str:
            cmd.append(args_str)
        if kwargs_str:
            cmd.append(kwargs_str)

        def dockerized(ctx: Context) -> None:
            with _setup_container(ctx):
                ctx.run(cmd, capture=False, silent=True)

        dockerized.__name__ = new_name
        dockerized.__doc__ = f"(Dockerized) {duty_instance.name or ''}"

        globals()[new_name] = duty(
            skip_if=_is_running_in_docker(),
            skip_reason=f"docker-exec-{duty_instance.name}: skipped => Running inside a Docker container",
        )(dockerized)
        return duty_instance

    return wrap_duty_for_docker_exec


# -----------------------------------------------------------------------------
# Commands --------------------------------------------------------------------
# -----------------------------------------------------------------------------


@duty(
    skip_if=_is_running_in_docker(),
    skip_reason="setup: skipped => Running inside a Docker container",
)
def setup(ctx: Context) -> None:
    """Set up the project environment.

    ```bash
    make setup
    ```

    Create a virtual environment using [uv](https://github.com/astral-sh/uv)
    and install the project dependencies, excluding development and editable installs.
    """
    _verify_uv_installed(ctx, "setup")
    ctx.run(
        ["uv", "sync", "--no-dev", "--no-editable"],
        title="Creating virtual environment using uv and installing the package",
    )


@duty(
    skip_if=_is_running_in_docker(),
    skip_reason="setup-dev: skipped => Running inside a Docker container",
)
def setup_dev(ctx: Context) -> None:
    """Set up the development environment using `uv` and configure pre-commit hooks.

    ```bash
    make setup-dev
    ```

    Create a virtual environment using [uv](https://github.com/astral-sh/uv), install
    the project dependencies, and configure pre-commit hooks for the development environment.
    """
    _verify_uv_installed(ctx, "setup_dev")
    ctx.run(
        ["uv", "sync"], title="Creating virtual environment using uv and installing the package"
    )
    ctx.run(["uv", "run", "pre-commit", "install", "-f"], title="Setting up pre-commit")


@duty(
    skip_if=_is_running_in_docker(),
    skip_reason="docker-build: skipped => Running inside a Docker container",
)
def docker_build(ctx: Context, env: str | None = None) -> None:
    """Build Docker images for the specified environment.

    ```bash
    make docker-build
    ```

    Use Docker Compose to build images for the selected environment (`dev` or `prod`).
    If no environment is provided, the user will be prompted to choose one.

    Args:
        env: The environment to build for (`dev` or `prod`). Defaults to `None` to prompt the user.
    """
    env = env or _pick_env(ctx, action="build")
    ctx.run(
        ["docker", "compose", "--profile", env, "build"],
        title=f"Building Docker images for {env} environment",
        capture=False,
    )


@duty(
    skip_if=_is_running_in_docker(),
    skip_reason="docker-start: skipped => Running inside a Docker container",
)
def docker_start(ctx: Context, env: str | None = None) -> None:
    """Start Docker containers for the specified environment.

    ```bash
    make docker-start
    ```

    Start the Docker containers using the specified environment (`dev` or `prod`).
    If no environment is provided, the user will be prompted to choose between `dev` and `prod`.

    Args:
        env: The environment to start (`dev` or `prod`). Defaults to `None` to prompt the user.
    """
    env = env or _pick_env(ctx)
    if env == "dev":
        ctx.run(
            "docker compose --profile dev up --watch > /dev/null 2>&1 &",
            title="Starting dev containers",
        )
    elif env == "prod":
        ctx.run(
            ["docker", "compose", "--profile", "prod", "up", "-d"], title="Starting prod containers"
        )
    while True:
        output = ctx.run(
            ["docker", "compose", "top"], silent=True, allow_overrides=False, capture=True
        )
        service = "fastapi-demo" if env == "prod" else "fastapi-demo-dev"
        if service in output:
            break
        time.sleep(0.5)


@duty(
    skip_if=_is_running_in_docker(),
    skip_reason="docker-stop: skipped => Running inside a Docker container",
)
def docker_stop(ctx: Context, env: str | None = None) -> None:
    """Stop and remove Docker containers for the specified environment.

    ```bash
    make docker-stop
    ```

    Stop and remove Docker containers using the specified environment (`dev` or `prod`).
    If no environment is provided, the user will be prompted to choose between them.

    Args:
        env: The environment to stop (`dev` or `prod`). Defaults to `None` to prompt the user.
    """
    env = env or _pick_env(ctx, action="stop")
    ctx.run(
        ["docker", "compose", "--profile", env, "down"],
        title=f"Stopping and removing {env} containers",
        capture=False,
    )


@dockerized_duty()
@duty(pre=["check-quality", "check-types", "check-docs", "check-api"])
def check(ctx: Context) -> None:
    """Check it all!

    ```bash
    make check
    ```

    Composite command to run all the check commands:

    - [`check-quality`][], to check the code quality on all Python versions
    - [`check-types`][], to type-check the code on all Python versions
    - [`check-docs`][], to check the docs on all Python versions
    - [`check-api`][], to check for API breaking changes
    """


@dockerized_duty()
@duty
def check_quality(ctx: Context) -> None:
    """Check the code quality.

    ```bash
    make check-quality
    ```

    Check the code quality using [Ruff](https://astral.sh/ruff).
    """
    ctx.run(
        tools.ruff.check(*PY_SRC_LIST, config="pyproject.toml"),
        title="Checking code quality [ruff]",
    )


@dockerized_duty()
@duty
def check_types(ctx: Context) -> None:
    """Check that the code is correctly typed.

    ```bash
    make check-types
    ```

    Run type-checking on the code with [Mypy](https://mypy.readthedocs.io/).
    """
    os.environ["FORCE_COLOR"] = "1"
    ctx.run(
        tools.mypy(*PY_SRC_LIST, config_file="pyproject.toml"),
        title="Type-checking [mypy]",
    )


@dockerized_duty()
@duty
def check_docs(ctx: Context) -> None:
    """Check if the documentation builds correctly.

    ```bash
    make check-docs
    ```

    Build the docs with [MkDocs](https://www.mkdocs.org/) in strict mode.

    The configuration for MkDocs is located at `mkdocs.yml`.

    This task builds the documentation with strict behavior:
    any warning will be considered an error and the command will fail.
    The warnings/errors can be about incorrect docstring format,
    or invalid cross-references.
    """
    ctx.run(
        tools.mkdocs.build(strict=True, verbose=True),
        title="Building documentation [mkdocs]",
    )


@dockerized_duty()
@duty(
    skip_if=_is_running_in_docker() and not shutil.which("git"),
    skip_reason="check-api: skipped => Running inside a Docker container that does not have git",
)
def check_api(ctx: Context, *cli_args: str) -> None:
    """Check for API breaking changes.

    ```bash
    make check-api
    ```

    Compare the current code to the latest version (Git tag)
    using [Griffe](https://mkdocstrings.github.io/griffe/),
    to search for API breaking changes since latest version.
    It is set to allow failures, and is more about providing information
    than preventing CI to pass.

    Parameters:
        *cli_args: Additional Griffe CLI arguments.
    """
    ctx.run(
        tools.griffe.check("fastapi_demo", search=["src"], color=True).add_args(*cli_args),
        title="Checking for API breaking changes [griffe]",
        nofail=True,
    )


@dockerized_duty()
@duty
def docs(ctx: Context, *cli_args: str, host: str = "127.0.0.1", port: int = 8080) -> None:
    """Serve the documentation (localhost:8080).

    ```bash
    make docs
    ```

    This task uses [MkDocs](https://www.mkdocs.org/) to serve the documentation locally.

    Parameters:
        *cli_args: Additional MkDocs CLI arguments.
        host: The host to serve the docs from.
        port: The port to serve the docs on.
    """
    ctx.run(
        tools.mkdocs.serve(dev_addr=f"{host}:{port}").add_args(*cli_args),
        title="Serving documentation",
        capture=False,
    )


@duty(
    skip_if=_is_running_in_docker(),
    skip_reason="docs-deploy: skipped => Running inside a Docker container",
)
def docs_deploy(ctx: Context) -> None:
    """Deploy the documentation to GitHub pages.

    ```bash
    make docs-deploy
    ```

    Use [MkDocs](https://www.mkdocs.org/) to build and deploy the documentation to GitHub pages.
    """
    os.environ["DEPLOY"] = "true"
    ctx.run(tools.mkdocs.gh_deploy(force=True), title="Deploying documentation")


@duty(
    skip_if=_is_running_in_docker(),
    skip_reason="format: skipped => Running inside a Docker container",
)
def format(ctx: Context) -> None:  # noqa: A001
    """Run formatting tools on the code.

    ```bash
    make format
    ```

    Format the code with [Ruff](https://astral.sh/ruff).
    This command will also automatically fix some coding issues when possible.
    """
    ctx.run(
        tools.ruff.check(*PY_SRC_LIST, config="pyproject.toml", fix_only=True, exit_zero=True),
        title="Auto-fixing code [ruff-linter]",
    )
    ctx.run(
        tools.ruff.format(*PY_SRC_LIST, config="pyproject.toml"),
        title="Formatting code [ruff-formatter]",
    )


@duty
def build(ctx: Context) -> None:
    """Build source and wheel distributions.

    ```bash
    make build
    ```

    Build distributions of your project for the current version.
    The `.tar.gz` (Gzipped sources archive) and `.whl` (wheel) distributions
    of your project can be found in the `dist` directory.
    """
    ctx.run(
        # tools.build(installer="uv"),
        ["uv", "build"],
        title="Building source and wheel distributions",
        pty=PTY,
    )


@duty
def clean_cache(ctx: Context) -> None:
    """Delete cache files.

    ```bash
    make clean_cache
    ```

    This command deletes cache directories such as `.pytest_cache/`, `.mypy_cache/`, etc.
    The virtual environment (.venv) is not removed by this command.
    """
    cache_dirs = [".cache", ".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__"]
    ctx.run(["rm", "-rf", *cache_dirs], title="Deleting cache files")


@duty
def clean(ctx: Context) -> None:
    """Delete build artifacts.

    ```bash
    make clean
    ```

    This command deletes build artifacts such as `dist/`, `site/`, etc.
    """
    paths_to_clean = ["build", "dist", "htmlcov", "site", ".coverage*", "coverage.xml"]
    ctx.run(f"rm -rf {' '.join(paths_to_clean)}", title="Deleting build artifacts")


@duty(
    skip_if=_is_running_in_docker(),
    skip_reason="release: skipped => Running inside a Docker container",
)
def release(ctx: Context, *cli_args: str) -> None:
    """Automate the full release process for a new project version.

    ```bash
    make release [OPTIONS]
    ```

    This task performs the following steps:
    1. Bumps the project version using Commitizen (`cz bump`), optionally with extra CLI arguments.
    2. Updates version references in files like `pyproject.toml`.
    3. Automatically generates or updates the `CHANGELOG.md` file (unless the default config was changed).
    4. Stages, commits, and tags the release in Git.
    5. Pushes the new commit and tag to the remote repository.
    6. Triggers post-tasks:
       - `clean`: Deletes build artifacts.
       - `build`: Generates source and wheel distributions.
       - `docs-deploy`: Publishes updated documentation to GitHub Pages.

    Parameters:
        *cli_args: Additional command-line arguments passed to `cz bump`
                   (e.g., `--increment patch`, `--dry-run`).
    """
    new_version = ctx.run(
        ["cz", "bump", "--get-next", "--yes", *[arg for arg in cli_args if arg != "--dry-run"]],
        silent=True,
        capture=True,
        allow_overrides=False,
        nofail=True,
    )

    dry_run = "--dry-run" in cli_args
    ctx.run(
        ["cz", "bump", "--yes", *cli_args],
        title=f"{'Dry-run: ' if dry_run else ''}Bumping project version to {new_version}",
        pty=PTY,
        nofail=dry_run,
    )

    if dry_run:
        ctx.run("false", title="Dry-run: no new commits and tags to push", nofail=True)
        ctx.run(
            "false",
            title="Dry-run: skipping clean, build, and docs deployment",
            nofail=True,
        )
        return

    output = ctx.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        title="Checking if an upstream is configured for the current branch",
        nofail=True,
        capture=True,
        allow_overrides=False,
    )
    is_upstream_set = "fatal" not in output
    if is_upstream_set:
        ctx.run(["git", "push"], title="Pushing commits", pty=False)
        ctx.run(["git", "push", "--tags"], title="Pushing tags", pty=False)
    else:
        ctx.run(
            "false",
            title="git-push: skipped => no upstream is configured for the current branch",
            nofail=True,
        )

    clean.run()
    build.run()
    if is_upstream_set:
        docs_deploy.run()
    else:
        ctx.run(
            "false", title="docs-deploy: skipped => the new release was not pushed", nofail=True
        )


@dockerized_duty()
@duty(aliases=["cov"])
def coverage(ctx: Context) -> None:
    """Report coverage as text, HTML and XML.

    ```bash
    make coverage
    ```

    Combine coverage data from multiple test runs with [Coverage.py](https://coverage.readthedocs.io/),
    then generate an HTML report into the `htmlcov` directory, an XML report into `coverage.xml`
    and print a text report in the console.
    """
    ctx.run(
        tools.coverage.combine(),
        nofail=True,
        title="Combining coverage data from multiple test runs",
    )
    ctx.run(tools.coverage.html(rcfile="pyproject.toml"), title="Creating an HTML report")
    ctx.run(tools.coverage.xml(rcfile="pyproject.toml"), title="Creating an XML report")
    ctx.run(
        tools.coverage.report(rcfile="pyproject.toml", show_missing=True),
        capture=False,
        title="Report coverage statistics",
    )


@dockerized_duty()
@duty(post=["cov"])
def test(ctx: Context, *cli_args: str, match: str | None = None) -> None:  # noqa: PT028
    """Run the test suite with doctests and coverage tracking.

    ```bash
    make test [match=EXPR]
    ```

    This task runs the `tests/` suite using [Pytest](https://docs.pytest.org/), with support for:
    - Embedded doctests via `--doctest-modules`
    - Coverage tracking using [Coverage.py](https://coverage.readthedocs.io/), configured through `pyproject.toml`
    - Optional test selection using `match=EXPR`, which maps to `-k EXPR`
    - Verbose output (`-vv`)

    Additional CLI arguments can be passed through `cli_args`.

    Parameters:
        *cli_args: Extra arguments to pass to Pytest.
        match: A pytest expression to filter which tests to run.
    """
    ctx.run(
        tools.pytest(
            "tests",
            config_file="pyproject.toml",
            select=match,
            color="yes",
            doctest_modules=True,  # Enable `--doctest-modules`
            verbosity=2,
        ).add_args(
            "--cov",
            "--cov-config=pyproject.toml",
            # "--cov-report=xml",
            # "--cov-report=term-missing",
            # "--cov-report=html",
            *cli_args,
        ),
        title="Running tests",
    )


@dockerized_duty()
@duty(post=["cov"])
def tox(ctx: Context) -> None:
    """Run the test suite in multiple Python environments using Tox.

    ```bash
    make tox
    ```

    Execute Tox with the `run-parallel` mode enabled to test the codebase across
    all configured Python environments concurrently (as defined in `tox.ini`).

    Once all environments have finished, the `cov` task is automatically triggered
    to combine and report test coverage from all runs.
    """
    ctx.run(["tox", "run-parallel"], title="Running Tox", capture=False)
