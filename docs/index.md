# fastapi-demo

[![Release](https://img.shields.io/github/v/release/bassemkaroui/fastapi-demo)](https://img.shields.io/github/v/release/bassemkaroui/fastapi-demo)
[![Build status](https://img.shields.io/github/actions/workflow/status/bassemkaroui/fastapi-demo/main.yml?branch=main)](https://github.com/bassemkaroui/fastapi-demo/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/bassemkaroui/fastapi-demo)](https://img.shields.io/github/commit-activity/m/bassemkaroui/fastapi-demo)
[![License](https://img.shields.io/github/license/bassemkaroui/fastapi-demo)](https://img.shields.io/github/license/bassemkaroui/fastapi-demo)

A demo API using FastAPI

# Installation

Griffe is a Python package, so you can install it with your favorite Python package installer or dependency manager.

TIP: **[Griffe Insiders](modules.md), a version with more features, is also available to sponsors :octicons-heart-fill-24:{ .heart .pulse }**


TIP: [Griffe Insiders](modules.md), a version with more features, is also available to sponsors :octicons-heart-fill-24:{ .heart .pulse }

> INFO: some info
>
> > WARNING: a warning

> IMPORTANT:
> **hi**

> INFO:
> **hi** there

INFO:
**hi** there

INFO: **hi** there

NOTE: some note

CAUTION: some caution

DANGER: a danger

ERROR: an error

SUCCESS: a success

QUESTION: a question

TODO: a todo

## Install as a tool & library

=== ":simple-python: pip"
    ```bash
    pip install griffe
    ```

    <div class="result" markdown>

    [pip](https://pip.pypa.io/en/stable/) is the main package installer for Python.

    </div>

=== ":simple-pdm: pdm"
    ```bash
    pdm add griffe
    ```

    <div class="result" markdown>

    [PDM](https://pdm-project.org/en/latest/) is an all-in-one solution for Python project management.

    </div>

=== ":simple-poetry: poetry"
    ```bash
    poetry add griffe
    ```

    <div class="result" markdown>

    [Poetry](https://python-poetry.org/) is an all-in-one solution for Python project management.

    </div>

=== ":simple-rye: rye"
    ```bash
    rye add griffe
    ```

    <div class="result" markdown>

    [Rye](https://rye.astral.sh/) is an all-in-one solution for Python project management, written in Rust.

    </div>

=== ":simple-astral: uv"
    ```bash
    uv add griffe
    ```

    <div class="result" markdown>

    [uv](https://docs.astral.sh/uv/) is an extremely fast Python package and project manager, written in Rust.

    </div>
## Code Annotation Examples

### Codeblocks

Some `code` goes here.

### Plain codeblock

A plain codeblock:

```
Some code here
def myfunction()
// some comment
```

#### Code for a specific language

Some more code with the `py` at the start:

``` py
import tensorflow as tf
def whatever()
```

#### With a title

``` py title="bubble_sort.py"
def bubble_sort(items):
    for i in range(len(items)):
        for j in range(len(items) - 1 - i):
            if items[j] > items[j + 1]:
                items[j], items[j + 1] = items[j + 1], items[j]
```

#### With line numbers

``` py linenums="1"
def bubble_sort(items):
    for i in range(len(items)):
        for j in range(len(items) - 1 - i):
            if items[j] > items[j + 1]:
                items[j], items[j + 1] = items[j + 1], items[j]
```

#### Highlighting lines

``` py hl_lines="2 3"
def bubble_sort(items: list[int]) -> None:
    for i in range(len(items)):
        for j in range(len(items) - 1 - i):
            if items[j] > items[j + 1]:
                items[j], items[j + 1] = items[j + 1], items[j]
```

## Icons and Emojs

:smile:

:fontawesome-regular-face-laugh-wink:

:fontawesome-brands-twitter:{ .twitter }

:octicons-heart-fill-24:{ .heart }
